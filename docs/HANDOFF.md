# Handoff: Voxcat Stage 1 (Historical)

## What was built

A voice AI agent (originally "Brainstorm Buddy") using Pipecat + Gemini Live + SmallWebRTC. See DESIGN.md for current plan.

**Working features:**
- Real-time voice conversation via browser (SmallWebRTC at `localhost:7860`)
- Gemini Live handles STT + LLM + TTS in one service
- Configurable voice (5 Gemini voices) and persona (3 profiles) via `config.yaml`
- Live transcript recording with timestamps
- Transcript saved to `brainstorms/YYYY-MM-DD-topic.md` on disconnect or Ctrl+C
- Summary template scaffolded (sections for key ideas, decisions, actions, open questions)

**Not yet built (Stage 1.5+):**
- LLM-generated summary (currently just template placeholders)
- Function calling (shell, files, NotebookLM CLI)
- MCP tools (Jira, Slack)
- Agent harness swap (Claude API, Hermes)
- Container deployment
- Multi-speaker diarization

## To run

```bash
cd ~/Documents/github.com/brainstorm-buddy
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
uv run python bot.py
# Open http://localhost:7860 in browser
```

## Prerequisites

- Python 3.13+
- `brew install portaudio` (macOS)
- Google Gemini API key from https://aistudio.google.com/apikey

## Design decisions

See the grilling session in the teaching workspace at `~/Documents/learning/pipecat/`. Key decisions:

- **Gemini Live** chosen for Stage 1 because it collapses STT+LLM+TTS into one service — simplest pipeline, fewest moving parts
- **SmallWebRTC** chosen over LocalAudioTransport for dev/prod parity — same transport in both environments
- **config.yaml** over .env for structured config (personas, voice selection)
- **Event handler transcript** over Observer pattern — simpler, aggregators already emit turn events
- **Summary template** deferred to Stage 1.5 when LLM function calling is available (will call Gemini to summarize the transcript)

## Next steps (Stage 1.5)

1. Add `@tool` or `FunctionSchema` handlers for shell commands and file operations
2. Wire `MCPClient` to Jira and Slack MCP servers
3. Add end-of-session LLM summary generation (send transcript back to Gemini, ask it to fill in the summary sections)
4. Add NotebookLM CLI integration via shell tool
5. Container deployment (Dockerfile + docker-compose)

## File structure

```
brainstorm-buddy/
├── bot.py              # Main bot
├── config.yaml         # Voice, persona, output config
├── .env.example        # API key template
├── .env                # Your API key (gitignored)
├── .gitignore
├── CONTEXT.md          # Domain glossary
├── AGENTS.md           # Agent guide
├── HANDOFF.md          # This file
├── pyproject.toml      # Dependencies
├── uv.lock
└── brainstorms/        # Output directory (gitignored, created at runtime)
```

## Learning workspace

Teaching materials at `~/Documents/learning/pipecat/`:
- Lessons 1-2 (frame pipeline mental model, first voice bot)
- Reference glossary
- Docker files (for future Pi deployment)
- Mission and learning records
