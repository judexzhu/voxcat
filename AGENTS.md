# AGENTS.md

## Project Overview

Voxcat is a voice AI agent built on Pipecat with swappable personas. Same pipeline handles brainstorming, SRE investigation, or any role — persona profiles control the system instruction, available tools, MCP servers, and output routing.

## Architecture

Two pipeline modes, configurable in `config.yaml`:

```
Live mode (~300ms latency):
  Browser (mic/speaker) ←WebRTC→ SmallWebRTCTransport
                                      ↓
                                user_aggregator
                                      ↓
                                GeminiLiveLLMService (STT+LLM+TTS + tools)
                                      ↓
                                transport.output()
                                      ↓
                                assistant_aggregator

Split mode (~800ms, smarter):
  Browser ←WebRTC→ SmallWebRTCTransport
                        ↓
                   GeminiSTTService (transcribe)
                        ↓
                   user_aggregator
                        ↓
                   GoogleLLMService (LLM + tools)
                        ↓
                   ResultSpillProcessor (large results → file)
                        ↓
                   GeminiTTSService (with optional style tags)
                        ↓
                   transport.output()
                        ↓
                   assistant_aggregator
```

RTVI observer reports tool calls to the frontend via WebRTC data channel.

## Key Files

| File | Purpose |
|------|---------|
| `src/voxcat/cli.py` | CLI entry point, HTTP routes, server startup |
| `src/voxcat/bot.py` | Pipeline orchestrator (live + split modes) |
| `src/voxcat/tools.py` | 11 tool handlers + `build_tools()` registry |
| `src/voxcat/transcript.py` | TranscriptRecorder (output + session files) |
| `src/voxcat/mcp_connect.py` | MCP server connection with read-only filter |
| `src/voxcat/filestore.py` | `safe_resolve()` for path traversal prevention |
| `src/voxcat/config.yaml.example` | Default config template |
| `client/src/` | React frontend (Vite + TypeScript) |

## Commands

```bash
# Install
uv tool install git+https://github.com/judexzhu/voxcat

# Run
voxcat init              # creates ~/.config/voxcat/config.yaml + .env
voxcat                   # start server on :7860

# Development
uv sync                  # install Python deps
cd client && npm ci      # install frontend deps
npm run dev              # frontend on :5173 with hot reload
uv run voxcat            # backend on :7860
```

## Output Directories

- Config: `~/.config/voxcat/`
- Data: `~/Documents/voxcat/`
  - `output/{persona}/` — per-persona files
  - `sessions/{persona}/` — session transcripts
  - `logs/` — daily log files

## Tests

```bash
uv run pytest tests/ -v         # run all tests
uv run pytest tests/test_filestore.py -v   # run one file
```

Key test files:
- `tests/test_filestore.py` — path traversal prevention (sibling prefix, absolute path)
- `tests/test_build_tools.py` — tool registration, API key gating, full tool count
- `tests/test_tts_pace.py` — TTS style tag prepending

## Code Style

Follow Pipecat conventions. Type hints. Async handlers.
