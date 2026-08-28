# AGENTS.md

## Project Overview

Voxcat is a voice AI agent built on Pipecat with swappable personas. Same pipeline handles brainstorming, SRE investigation, or any role — persona profiles control the system instruction, available tools, MCP servers, and output routing.

## Architecture

```
Browser (mic/speaker) ←WebRTC→ SmallWebRTCTransport
                                    ↓
                              user_aggregator (tracks user turns)
                                    ↓
                              GeminiLiveLLMService (STT+LLM+TTS + function calling)
                                    ↓
                              SmallWebRTCTransport output
                                    ↓
                              assistant_aggregator (tracks bot turns)

Tools: WebSearch (Tavily) | File read/write | MCP (Red Hat, Jira) | NotebookLM
Event handlers on aggregators → TranscriptRecorder → output dir
```

## Key Files

| File | Purpose |
|------|---------|
| `bot.py` | Main bot — pipeline, transport, tools, transcript recording |
| `config.yaml` | Voice, persona profiles (instruction + tools + output), server settings |
| `.env` | API keys (`GOOGLE_API_KEY`, `TAVILY_API_KEY`) |
| `DESIGN.md` | Architecture decisions and implementation plan |
| `brainstorms/` | Default output directory for brainstorm sessions |

## Commands

```bash
uv run python bot.py
# Opens at http://localhost:7860
# Persona selection: http://localhost:7860?persona=sre
```

## Staging Plan

| Stage | What |
|-------|------|
| 1 (done) | Gemini Live + SmallWebRTC + transcript + personas |
| 1.5 (current) | Function calling, WebSearch, file ops, MCP (Red Hat + Jira read-only), LLM summary |
| 2 | CLI tools, NotebookLM sync, container deployment |

## Code Style

Follow Pipecat conventions. Type hints for async code. Single bot.py until ~300 lines.

## Agent skills

### Issue tracker

Issues tracked as local markdown under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at root. See `docs/agents/domain.md`.
