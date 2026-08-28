import os
import signal
from datetime import datetime
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
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.mcp_service import MCPClient
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.workers.runner import WorkerRunner

load_dotenv(override=True)



def load_config():
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


class TranscriptRecorder:
    """Records conversation turns and generates summary at session end."""

    def __init__(self, output_dir: str):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._turns: list[dict] = []
        self._session_start = datetime.now()
        self._topic = "untitled"

    def add_turn(self, role: str, content: str, timestamp: datetime | None = None):
        self._turns.append({
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now(),
        })

    def set_topic(self, topic: str):
        self._topic = topic

    def save_transcript(self) -> Path:
        date_str = self._session_start.strftime("%Y-%m-%d")
        slug = self._topic.lower().replace(" ", "-")[:40]
        filename = f"{date_str}-{slug}.md"
        filepath = self._output_dir / filename

        duration = datetime.now() - self._session_start
        minutes = int(duration.total_seconds() // 60)

        lines = [
            f"# Brainstorm: {self._topic}",
            f"**Date:** {date_str}  |  **Duration:** {minutes}m",
            "",
            "## Key Ideas",
            "- *(review transcript below and fill in)*",
            "",
            "## Decisions Made",
            "- *(review transcript below and fill in)*",
            "",
            "## Action Items",
            "- [ ] *(review transcript below and fill in)*",
            "",
            "## Open Questions",
            "- *(review transcript below and fill in)*",
            "",
            "## Raw Transcript",
            "",
        ]

        for turn in self._turns:
            ts = turn["timestamp"]
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%H:%M:%S")
            role = turn["role"].capitalize()
            lines.append(f"**[{ts}] {role}:** {turn['content']}")
            lines.append("")

        filepath.write_text("\n".join(lines))
        return filepath

    def get_transcript_text(self) -> str:
        lines = []
        for turn in self._turns:
            ts = turn["timestamp"]
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%H:%M:%S")
            lines.append(f"[{ts}] {turn['role'].capitalize()}: {turn['content']}")
        return "\n".join(lines)


async def web_search_handler(params: FunctionCallParams):
    from tavily import AsyncTavilyClient

    query = params.arguments["query"]
    logger.info(f"WebSearch: {query}")
    client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    response = await client.search(query=query, max_results=5)
    results = [
        {"title": r["title"], "url": r["url"], "content": r["content"][:500]}
        for r in response.get("results", [])
    ]
    await params.result_callback({"results": results})


async def get_current_time_handler(params: FunctionCallParams):
    now = datetime.now()
    await params.result_callback({
        "datetime": now.isoformat(),
        "readable": now.strftime("%A, %B %d, %Y at %I:%M %p"),
    })


async def deep_analysis_handler(params: FunctionCallParams):
    from google import genai

    query = params.arguments["query"]
    context = params.arguments.get("context", "")
    logger.info(f"DeepAnalysis: {query[:100]}")
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    prompt = f"{query}\n\nContext:\n{context}" if context else query
    response = await client.aio.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            thinking_config=genai.types.ThinkingConfig(thinking_budget=8192),
        ),
    )
    await params.result_callback({"analysis": response.text[:5000]})


async def research_handler(params: FunctionCallParams):
    from google import genai
    from tavily import AsyncTavilyClient

    topic = params.arguments["topic"]
    logger.info(f"Research: {topic}")
    tavily = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    search_response = await tavily.search(query=topic, max_results=5)
    results = search_response.get("results", [])
    logger.info(f"Research: found {len(results)} search results")

    urls = [r["url"] for r in results[:3]]
    extracted = []
    if urls:
        extract_response = await tavily.extract(urls=urls)
        for r in extract_response.get("results", []):
            extracted.append({"url": r["url"], "content": r["raw_content"][:3000]})
    logger.info(f"Research: extracted {len(extracted)} pages")

    sources_text = "\n\n".join(
        f"Source: {e['url']}\n{e['content']}" for e in extracted
    )
    snippets_text = "\n".join(
        f"- {r['title']}: {r['content'][:200]}" for r in results
    )

    prompt = (
        f"Research topic: {topic}\n\n"
        f"Search snippets:\n{snippets_text}\n\n"
        f"Full page content:\n{sources_text}\n\n"
        "Synthesize a structured research report with: Key Findings, Details, Sources, and Open Questions."
    )

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = await client.aio.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            thinking_config=genai.types.ThinkingConfig(thinking_budget=8192),
        ),
    )
    await params.result_callback({"report": response.text[:5000]})


async def notebooklm_sync_handler(params: FunctionCallParams):
    from notebooklm import NotebookLMClient

    title = params.arguments["title"]
    content = params.arguments["content"]
    notebook_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "")
    if not notebook_id:
        await params.result_callback({"error": "NOTEBOOKLM_NOTEBOOK_ID not set"})
        return
    logger.info(f"NotebookLM sync: {title}")
    async with NotebookLMClient.from_storage() as client:
        await client.sources.add_text(
            notebook_id=notebook_id, title=title, content=content, wait=True,
        )
    await params.result_callback({"status": "synced", "notebook_id": notebook_id, "title": title})


def build_tools(
    builtin_tools: list[str], output_dir: str, recorder: TranscriptRecorder,
) -> list[FunctionSchema]:
    output_path = Path(output_dir).resolve()

    async def web_read_handler(params: FunctionCallParams):
        from tavily import AsyncTavilyClient

        url = params.arguments["url"]
        logger.info(f"WebRead: {url}")
        client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = await client.extract(urls=[url])
        results = response.get("results", [])
        content = results[0]["raw_content"][:5000] if results else "Failed to extract content"
        await params.result_callback({"url": url, "content": content})

    async def file_read_handler(params: FunctionCallParams):
        filename = params.arguments["filename"]
        path = (output_path / filename).resolve()
        if not str(path).startswith(str(output_path)):
            await params.result_callback({"error": "Access denied: path outside output directory"})
            return
        if not path.exists():
            await params.result_callback({"error": f"File not found: {filename}"})
            return
        await params.result_callback({"filename": filename, "content": path.read_text()[:5000]})

    async def file_write_handler(params: FunctionCallParams):
        filename = params.arguments["filename"]
        content = params.arguments["content"]
        path = (output_path / filename).resolve()
        if not str(path).startswith(str(output_path)):
            await params.result_callback({"error": "Access denied: path outside output directory"})
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        logger.info(f"File written: {path}")
        await params.result_callback({"status": "saved", "path": str(path), "content": content[:3000]})

    async def file_list_handler(params: FunctionCallParams):
        files = sorted(output_path.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        entries = [{"name": f.name, "size": f.stat().st_size} for f in files[:20]]
        await params.result_callback({"directory": str(output_path), "files": entries})

    async def summarize_handler(params: FunctionCallParams):
        transcript = recorder.get_transcript_text()
        if not transcript:
            await params.result_callback({"error": "No transcript recorded yet"})
            return
        await params.result_callback({
            "transcript": transcript[:10000],
            "instruction": "Summarize into: Key Ideas, Decisions, Action Items, Open Questions",
        })

    available = {}

    if os.environ.get("TAVILY_API_KEY"):
        available["websearch"] = FunctionSchema(
            name="web_search",
            description="Search the web for real-time information, documentation, or any topic",
            properties={"query": {"type": "string", "description": "Search query"}},
            required=["query"], handler=web_search_handler,
        )
        available["web_read"] = FunctionSchema(
            name="web_read",
            description="Read and extract the full content of a web page given its URL",
            properties={"url": {"type": "string", "description": "URL to read"}},
            required=["url"], handler=web_read_handler,
        )

    available["file_read"] = FunctionSchema(
        name="file_read",
        description="Read a file from the session output directory (past transcripts, notes)",
        properties={"filename": {"type": "string", "description": "Name of the file to read"}},
        required=["filename"], handler=file_read_handler,
    )
    available["file_write"] = FunctionSchema(
        name="file_write",
        description="Save content to a file in the session output directory",
        properties={
            "filename": {"type": "string", "description": "Name of the file to save"},
            "content": {"type": "string", "description": "Content to write"},
        },
        required=["filename", "content"], handler=file_write_handler,
    )
    available["file_list"] = FunctionSchema(
        name="file_list",
        description="List files in the session output directory",
        properties={}, required=[], handler=file_list_handler,
    )
    available["summarize_session"] = FunctionSchema(
        name="summarize_session",
        description="Get the current session transcript for summarization. Summarize into: Key Ideas, Decisions Made, Action Items, and Open Questions",
        properties={}, required=[], handler=summarize_handler,
    )
    available["get_current_time"] = FunctionSchema(
        name="get_current_time",
        description="Get the current date and time",
        properties={}, required=[], handler=get_current_time_handler,
    )
    available["deep_analysis"] = FunctionSchema(
        name="deep_analysis",
        description="Send a complex question to a powerful reasoning model for deep analysis. Use for root cause analysis, complex troubleshooting, or when you need thorough reasoning",
        properties={
            "query": {"type": "string", "description": "The question or analysis request"},
            "context": {"type": "string", "description": "Supporting context (case details, logs, error messages)"},
        },
        required=["query"], handler=deep_analysis_handler,
    )
    if os.environ.get("TAVILY_API_KEY"):
        available["research"] = FunctionSchema(
            name="research",
            description="Research a topic thoroughly: search the web, read top sources, and synthesize a structured report with Key Findings, Details, Sources, and Open Questions. Takes 10-15 seconds.",
            properties={
                "topic": {"type": "string", "description": "The topic or question to research"},
            },
            required=["topic"], handler=research_handler,
        )

    if os.environ.get("NOTEBOOKLM_NOTEBOOK_ID"):
        available["notebooklm_sync"] = FunctionSchema(
            name="notebooklm_sync",
            description="Sync a document to Google NotebookLM as a text source. Use for archiving case reports, research findings, or session summaries to the knowledge base.",
            properties={
                "title": {"type": "string", "description": "Title of the document"},
                "content": {"type": "string", "description": "Full markdown content to sync"},
            },
            required=["title", "content"], handler=notebooklm_sync_handler,
        )

    tools = []
    for name in builtin_tools:
        if name in available:
            tools.append(available[name])
            logger.info(f"Tool registered: {name}")
        else:
            logger.warning(f"Tool not available: {name} (missing API key or not implemented)")
    return tools


async def connect_mcp_servers(
    server_names: list[str], mcp_config: dict,
) -> tuple[list, list[MCPClient]]:
    from mcp import StdioServerParameters

    all_tools = []
    clients = []
    for name in server_names:
        server = mcp_config.get(name)
        if not server:
            logger.warning(f"MCP server not configured: {name}")
            continue
        env_keys = server.get("env_keys", [])
        missing = [k for k in env_keys if not os.environ.get(k)]
        if missing:
            logger.warning(f"MCP server {name} skipped: missing env vars {missing}")
            continue
        env = {k: os.environ[k] for k in env_keys if os.environ.get(k)}
        env["PATH"] = os.environ.get("PATH", "")
        cwd = server.get("cwd")
        client = MCPClient(
            server_params=StdioServerParameters(
                command=server["command"],
                args=server.get("args", []),
                env=env,
                cwd=cwd,
            ),
            tools_filter=server.get("read_only_tools"),
        )
        try:
            mcp_tools = await client.tools()
            tool_list = mcp_tools.standard_tools
            all_tools.extend(tool_list)
            clients.append(client)
            logger.info(f"MCP server {name}: {len(tool_list)} tools registered")
        except Exception as e:
            logger.error(f"MCP server {name} failed to connect: {e}")
    return all_tools, clients


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
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms")).resolve()
        path = (output_dir / filename).resolve()
        if not str(path).startswith(str(output_dir)) or not path.exists():
            return {"error": "File not found"}
        return {"filename": filename, "content": path.read_text()[:10000]}

    client_dist = Path(__file__).parent / "client" / "dist"
    if client_dist.is_dir():
        app.mount("/client", StaticFiles(directory=str(client_dist), html=True))

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/client/")

    main()
