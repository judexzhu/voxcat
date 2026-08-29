import os
import signal
from pathlib import Path

import yaml
from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker, ProcessorUnusablePolicy
from pipecat.processors.frameworks.rtvi import RTVIFunctionCallReportLevel, RTVIObserverParams
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    AssistantTurnStoppedMessage,
    LLMContextAggregatorPair,
    UserTurnMessageAddedMessage,
)
from pipecat.runner.types import RunnerArguments
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

from filestore import safe_resolve
from mcp_connect import connect_mcp_servers
from tools import build_tools
from transcript import TranscriptRecorder

load_dotenv(override=True)


def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    config = load_config()

    body = runner_args.body or {}
    persona_name = body.get("persona") or config["persona"]["default"]
    if persona_name not in config["persona"]["profiles"]:
        logger.warning(f"Unknown persona '{persona_name}', falling back to default")
        persona_name = config["persona"]["default"]
    persona = config["persona"]["profiles"][persona_name]
    common = config["persona"].get("common_instruction", "")
    system_instruction = persona["instruction"] + "\n" + common if common else persona["instruction"]
    voice = config["voice"]["name"]
    output_dir = persona.get("output", {}).get("directory", "brainstorms")
    builtin_tools = persona.get("tools", {}).get("builtin", [])
    mcp_server_names = persona.get("tools", {}).get("mcp_servers", [])

    recorder = TranscriptRecorder(output_dir)
    tools = build_tools(builtin_tools, output_dir, recorder)

    mcp_clients = []
    if mcp_server_names:
        mcp_config = config.get("mcp_servers", {})
        mcp_tools, mcp_clients = await connect_mcp_servers(mcp_server_names, mcp_config)
        tools.extend(mcp_tools)

    logger.info(f"Persona: {persona_name} | Tools: {len(tools)} | Output: {output_dir}")

    llm = GeminiLiveLLMService(
        api_key=os.environ["GOOGLE_API_KEY"],
        settings=GeminiLiveLLMService.Settings(
            system_instruction=system_instruction,
            voice=voice,
        ),
    )

    context = LLMContext(tools=tools)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    pipeline = Pipeline([
        transport.input(),
        user_aggregator,
        llm,
        transport.output(),
        assistant_aggregator,
    ])

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        rtvi_observer_params=RTVIObserverParams(
            function_call_report_level={"*": RTVIFunctionCallReportLevel.FULL},
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
        processor_unusable_policy=ProcessorUnusablePolicy.END,
    )

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)
    await runner.add_workers(worker)

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected — starting {persona_name} session")
        context.add_message({
            "role": "developer",
            "content": "Greet the user briefly. Introduce yourself based on your role. "
            "Ask what they'd like to work on today.",
        })
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        filepath = recorder.save_transcript()
        logger.info(f"Transcript saved to {filepath}")
        for mc in mcp_clients:
            await mc.close()
        await runner.cancel()

    @user_aggregator.event_handler("on_user_turn_message_added")
    async def on_user_turn_message_added(aggregator, message: UserTurnMessageAddedMessage):
        recorder.add_turn("user", message.content, message.timestamp)
        timestamp = f"[{message.timestamp}] " if message.timestamp else ""
        logger.info(f"Transcript: {timestamp}user: {message.content}")

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message: AssistantTurnStoppedMessage):
        recorder.add_turn("assistant", message.content, message.timestamp)
        timestamp = f"[{message.timestamp}] " if message.timestamp else ""
        logger.info(f"Transcript: {timestamp}assistant: {message.content}")

    def handle_shutdown(signum, frame):
        filepath = recorder.save_transcript()
        logger.info(f"Transcript saved to {filepath}")

    signal.signal(signal.SIGINT, handle_shutdown)

    await runner.run()


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat runner."""
    webrtc_connection: SmallWebRTCConnection = runner_args.webrtc_connection

    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    )

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from fastapi.staticfiles import StaticFiles

    from pipecat.runner.run import app, main

    config = load_config()
    available_personas = list(config["persona"]["profiles"].keys())

    @app.get("/api/personas")
    async def list_personas():
        return {"personas": available_personas, "default": config["persona"]["default"]}

    @app.get("/api/files/tree")
    async def file_tree():
        tree = []
        for name in available_personas:
            profile = config["persona"]["profiles"][name]
            output_dir = Path(profile.get("output", {}).get("directory", f"output/{name}"))
            output_dir.mkdir(parents=True, exist_ok=True)
            files = sorted(output_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
            tree.append({
                "persona": name,
                "label": {"thinking-partner": "Thinking Partner", "devils-advocate": "Devil's Advocate",
                          "note-taker": "Note Taker", "sre": "SRE Assistant"}.get(name, name),
                "files": [
                    {"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
                    for f in files[:50] if f.is_file()
                ],
            })
        return {"tree": tree}

    @app.get("/api/files")
    async def list_files(persona: str = "thinking-partner"):
        profile = config["persona"]["profiles"].get(persona, {})
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms"))
        output_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(output_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        return {
            "directory": str(output_dir),
            "files": [
                {"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
                for f in files[:50] if f.is_file()
            ],
        }

    @app.get("/api/files/{filename:path}")
    async def read_file(filename: str, persona: str = "thinking-partner"):
        profile = config["persona"]["profiles"].get(persona, {})
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms"))
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        return {"filename": filename, "content": path.read_text()[:10000]}

    notebook_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "")

    @app.get("/api/notebooklm/sources")
    async def nlm_sources():
        if not notebook_id:
            return {"sources": []}
        try:
            from notebooklm import NotebookLMClient
            async with NotebookLMClient.from_storage() as client:
                sources = await client.sources.list(notebook_id)
                return {"sources": [
                    {"id": s.id, "title": s.title}
                    for s in sources
                ]}
        except Exception as e:
            logger.error(f"NotebookLM sources error: {e}")
            return {"sources": []}

    @app.get("/api/notebooklm/sources/{source_id}")
    async def nlm_source_content(source_id: str):
        if not notebook_id:
            return {"error": "NotebookLM not configured"}
        try:
            from notebooklm import NotebookLMClient
            async with NotebookLMClient.from_storage() as client:
                fulltext = await client.sources.get_fulltext(notebook_id, source_id, output_format="markdown")
                return {"content": fulltext.content[:20000]}
        except Exception as e:
            logger.error(f"NotebookLM source read error: {e}")
            return {"error": str(e)}

    client_dist = Path(__file__).parent / "client" / "dist"
    if client_dist.is_dir():
        app.mount("/client", StaticFiles(directory=str(client_dist), html=True))

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/client/")

    main()
