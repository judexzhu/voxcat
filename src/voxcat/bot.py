import os
from pathlib import Path

import yaml
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

import json
import re
from datetime import datetime

from pipecat.frames.frames import FunctionCallResultFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from .mcp_connect import connect_mcp_servers
from .tools import build_tools
from .transcript import TranscriptRecorder

TOOL_ROUTING = {
    "deep_analysis": 'Questions with "why", "root cause", "analyze", "compare", "trade-offs" → ALWAYS call deep_analysis.\n'
                     'User says "think deeper" or "analyze this" → call deep_analysis immediately.',
    "research": 'User says "research" or "look into" → call research. It searches, reads sources, and synthesizes a report.',
    "websearch": "Factual question → call web_search. Never guess.",
    "web_read": "URL in search results looks useful → call web_read on it.",
    "set_topic": 'After the first substantive exchange, call set_topic with a short descriptive slug for this session (e.g. "ai-sre-exploration"). Do this once, silently — don\'t announce it.',
    "summarize_session": 'User says "wrap up", "summarize", "done", "that\'s all for today" → call summarize_session. It saves the summary silently — don\'t read it aloud, just confirm it\'s saved.',
    "notebooklm_sync": 'User says "sync to notebook", "push to NotebookLM", or "archive this" → call notebooklm_sync with the content.',
    "get_current_time": "When asked the time, call get_current_time.",
}

COMMON_INSTRUCTION_BASE = (
    "Before calling ANY tool, say a brief phrase like \"Let me check\", \"Looking that up\", \"One moment\" — never go silent while a tool runs.\n"
    "NEVER call the same tool twice with the same arguments. If a tool already returned results, use those results — do not re-call it.\n"
    "After a tool returns, ALWAYS speak the result to the user before calling another tool.\n"
    "When asked to save, don't confirm — just save."
)


def build_common_instruction(registered_tool_names: set[str]) -> str:
    lines = [COMMON_INSTRUCTION_BASE]
    for tool_key, routing_line in TOOL_ROUTING.items():
        if tool_key in registered_tool_names:
            lines.append(routing_line)
    return "\n".join(lines)

TTS_STYLES = ("extremely fast", "whispering", "shouting", "sarcasm", "robotic")


class ResultSpillProcessor(FrameProcessor):
    # ponytail: 5000 char threshold is a workaround — needs real usage data to find optimal value
    def __init__(self, output_dir: str, threshold: int = 5000, preview_size: int = 2000):
        super().__init__()
        self._output_dir = Path(output_dir) / "tool-results"
        self._threshold = threshold
        self._preview_size = preview_size

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)
        if isinstance(frame, FunctionCallResultFrame) and direction == FrameDirection.DOWNSTREAM:
            serialized = json.dumps(frame.result, default=str, ensure_ascii=False)
            if len(serialized) > self._threshold:
                self._output_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                filename = f"{frame.function_name}-{ts}.json"
                filepath = self._output_dir / filename
                filepath.write_text(serialized)
                frame.result = {
                    "preview": serialized[:self._preview_size],
                    "truncated": True,
                    "full_size_chars": len(serialized),
                    "full_result_file": f"tool-results/{filename}",
                    "note": "Result too large. Preview shown. Use file_read to see the full data.",
                }
                logger.info(f"Tool result spilled to {filepath} ({len(serialized)} chars)")
        await self.push_frame(frame, direction)


def apply_tts_style(tts_service, style: str):
    """Monkey-patch run_tts to prepend a style tag to every sentence."""
    tag = f"[{style}] "
    original_run = tts_service.run_tts

    async def styled_run_tts(text, context_id):
        if text.strip():
            text = tag + text
        async for frame in original_run(text, context_id):
            yield frame

    tts_service.run_tts = styled_run_tts


_config = None


def load_config(config_path: str | Path | None = None):
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def set_config(config: dict):
    global _config
    _config = config


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    config = _config or load_config()

    body = runner_args.body or {}
    persona_name = body.get("persona") or config["persona"]["default"]
    if persona_name not in config["persona"]["profiles"]:
        logger.warning(f"Unknown persona '{persona_name}', falling back to default")
        persona_name = config["persona"]["default"]
    persona = config["persona"]["profiles"][persona_name]
    voice_config = config["voice"]
    voice_mode = voice_config.get("mode", "live")
    output_dir = persona.get("output", {}).get("directory", f"output/{persona_name}")
    builtin_tools = persona.get("tools", {}).get("builtin", [])
    mcp_server_names = persona.get("tools", {}).get("mcp_servers", [])

    recorder = TranscriptRecorder(output_dir, persona=persona_name)
    tools_config = config.get("tools", {})
    tools = build_tools(builtin_tools, output_dir, recorder, tools_config=tools_config)

    mcp_clients = []
    if mcp_server_names:
        mcp_config = config.get("mcp_servers", {})
        mcp_tools, mcp_clients = await connect_mcp_servers(mcp_server_names, mcp_config)
        tools.extend(mcp_tools)

    registered_names = set(builtin_tools) | {t.name for t in tools}
    common = build_common_instruction(registered_names)
    system_instruction = f"{common}\n\n{persona['instruction']}"

    is_silent = persona.get("silent", False)
    if is_silent and voice_mode == "live":
        logger.warning(f"Persona '{persona_name}' is silent but live mode cannot mute TTS — auto-switching to split mode")
        voice_mode = "split"
    logger.info(f"Persona: {persona_name} | Mode: {voice_mode} | Silent: {is_silent} | Tools: {len(tools)} | Output: {output_dir}")

    result_spill = ResultSpillProcessor(output_dir)

    context = LLMContext(tools=tools)
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(context)

    if voice_mode == "split":
        from pipecat.services.google.gemini_live.stt import GeminiSTTService
        from pipecat.services.google.llm import GoogleLLMService
        from pipecat.services.google.tts import GeminiTTSService

        split_config = voice_config.get("split", {})
        api_key = os.environ["GOOGLE_API_KEY"]

        stt = GeminiSTTService(
            api_key=api_key,
            model=split_config.get("stt_model", "gemini-3.5-transcribe-live"),
        )
        llm = GoogleLLMService(
            api_key=api_key,
            model=split_config.get("llm_model", "gemini-3.7-flash"),
            settings=GoogleLLMService.Settings(
                system_instruction=system_instruction,
            ),
        )
        if is_silent:
            pipeline = Pipeline([
                transport.input(),
                stt,
                user_aggregator,
                llm,
                result_spill,
                transport.output(),
                assistant_aggregator,
            ])
        else:
            tts = GeminiTTSService(
                api_key=api_key,
                model=split_config.get("tts_model", "gemini-3.1-flash-tts-preview"),
                voice_id=split_config.get("tts_voice", "Aoede"),
            )

            tts_style = split_config.get("tts_style")
            if tts_style:
                if tts_style in TTS_STYLES:
                    apply_tts_style(tts, tts_style)
                else:
                    logger.warning(f"Unknown tts_style '{tts_style}' — ignored. Valid: {', '.join(TTS_STYLES)}")

            pipeline = Pipeline([
                transport.input(),
                stt,
                user_aggregator,
                llm,
                result_spill,
                tts,
                transport.output(),
                assistant_aggregator,
            ])
    else:
        llm = GeminiLiveLLMService(
            api_key=os.environ["GOOGLE_API_KEY"],
            model=voice_config.get("live", {}).get("model", "gemini-3.1-flash-live-preview"),
            settings=GeminiLiveLLMService.Settings(
                system_instruction=system_instruction,
                voice=voice_config.get("live", {}).get("voice", "Aoede"),
            ),
        )

        pipeline = Pipeline([
            transport.input(),
            user_aggregator,
            llm,
            result_spill,
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

    prior_context = body.get("context", "")

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected — starting {persona_name} session")
        if is_silent:
            logger.info("Silent persona — skipping greeting")
        elif prior_context:
            context.add_message({
                "role": "developer",
                "content": f"The user is continuing a previous session. Here is the transcript:\n\n{prior_context}\n\n"
                "Welcome them back briefly. Reference what was discussed. Ask what they'd like to continue with.",
            })
            await worker.queue_frames([LLMRunFrame()])
        else:
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
        session_file = body.get("session_file")
        session_path = recorder.save_session(append_to=session_file)
        logger.info(f"Session saved to {session_path}")
        for mc in mcp_clients:
            await mc.close()
        await runner.cancel()

    @user_aggregator.event_handler("on_user_turn_message_added")
    async def on_user_turn_message_added(aggregator, message: UserTurnMessageAddedMessage):
        recorder.add_turn("user", message.content, message.timestamp)
        timestamp = f"[{message.timestamp}] " if message.timestamp else ""
        logger.info(f"Transcript: {timestamp}user: {message.content}")

    _style_tag_re = re.compile(r"\[(?:" + "|".join(re.escape(s) for s in TTS_STYLES) + r")\]\s?")

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message: AssistantTurnStoppedMessage):
        clean = _style_tag_re.sub("", message.content)
        recorder.add_turn("assistant", clean, message.timestamp)
        timestamp = f"[{message.timestamp}] " if message.timestamp else ""
        logger.info(f"Transcript: {timestamp}assistant: {clean}")
        # Strip style tags from LLM context so model doesn't reproduce them
        for msg in context.messages:
            if not isinstance(msg, dict):
                continue
            for part in msg.get("parts", []):
                if isinstance(part, dict) and "text" in part and _style_tag_re.search(part["text"]):
                    part["text"] = _style_tag_re.sub("", part["text"])

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


