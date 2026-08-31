# Voxcat

A voice AI agent with swappable personas. Talk to it, it calls tools, writes files, and remembers what you discussed.

Built on [Pipecat](https://github.com/pipecat-ai/pipecat) + Gemini Live + SmallWebRTC.

![Landing](docs/preview-landing.png)

![Session](docs/preview-session.png)

![Architecture](docs/voxcat-architecture.visual-check.2048x1320.dark.png)

## What it does

- **Voice-first**: speak naturally, get spoken responses
- **Personas**: switch roles (Thinking Partner, Devil's Advocate, Note Taker, SRE Assistant) with different instructions and tool sets
- **11 built-in tools**: web search, web read, file read/write/list, deep analysis (Gemini 3.7 Flash), research, session summary, NotebookLM sync, set topic, current time
- **Persona files**: each persona is a markdown file with YAML frontmatter — instruction, tool set, voice identity, greeting, output directory
- **MCP integration**: connect external tool servers with read-only enforcement (e.g. [redhat-api-mcp](https://github.com/judexzhu/redhat-api-mcp), [mcp-jira](https://github.com/judexzhu/mcp-jira))
- **Per-persona output**: each persona writes to its own folder
- **Session continuity**: past sessions saved as markdown, continue any session with full context injected

## Architecture

Two pipeline modes, configurable in `config.yaml`:

```
Live mode (~300ms latency):
  mic -> Gemini 3.1 Flash Live (STT+LLM+TTS) -> speaker

Split mode (~800ms, smarter):
  mic -> Gemini 3.5 Transcribe Live (STT)
       -> Gemini 3.7 Flash (LLM + tools)
       -> Gemini 3.1 Flash TTS -> speaker
```

Frontend connects via WebRTC. RTVI data channel carries transcripts and tool call events.

## Prerequisites

| Requirement | Version | Check | Install |
|---|---|---|---|
| Python | 3.13+ | `python3 --version` | [python.org](https://www.python.org/downloads/) |
| uv | any | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Google API key | — | [Google AI Studio](https://aistudio.google.com/apikey) | Free tier works |

Optional for extra tools:

| Key | Tool |
|---|---|
| `TAVILY_API_KEY` | Web search + web read |
| `NOTEBOOKLM_NOTEBOOK_ID` | Sync documents to Google NotebookLM |

## Quick start

```bash
# 1. Install
uv tool install git+https://github.com/judexzhu/voxcat

# 2. Initialize config, env, and persona files
voxcat init
# Output:
#   created ~/.config/voxcat/config.yaml
#   created ~/.config/voxcat/.env
#   created ~/.config/voxcat/personas/ (4 personas)

# 3. Add your API key
# Open ~/.config/voxcat/.env and set:
#   GOOGLE_API_KEY=your-key-here

# 4. Start
voxcat
```

Open `http://localhost:7860`, select a persona, start talking.

Files created during sessions go to `~/Documents/voxcat/`.

### Development

For working on voxcat itself (frontend hot reload, local Python changes):

```bash
git clone https://github.com/judexzhu/voxcat && cd voxcat
uv sync                              # Python deps

# Terminal 1 — backend (picks up local source changes)
uv run voxcat                        # serves on :7860

# Terminal 2 — frontend (hot reload)
cd client && npm ci && npm run dev   # serves on :5173, proxies API to :7860
```

## Configuration

Config lives at `~/.config/voxcat/`. Run `voxcat init` to create it.

### Personas

Each persona is a markdown file in `~/.config/voxcat/personas/`:

```markdown
---
label: "Thinking Partner"
description: "Probing questions, challenged assumptions."
greeting: "What's on your mind?"
voice:
  tts_voice: "Aoede"
  tts_style: "extremely fast"
tools:
  builtin: [websearch, web_read, file_read, file_write, file_list, ...]
  mcp_servers: []
output:
  directory: "output/thinking-partner"
---

You are a brainstorming partner. Under 50 words per response...
```

Ships with 4 personas: `thinking-partner`, `devils-advocate`, `note-taker`, `sre`.

Create your own by adding a `.md` file to `~/.config/voxcat/personas/`. Filename becomes the slug (e.g. `my-coach.md` → persona `my-coach`). Files starting with `_` are skipped.

#### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `label` | Yes | Display name in UI |
| `description` | No | One-line shown in persona selector |
| `greeting` | No | Exact first message spoken on connect |
| `silent` | No | `true` for listen-only personas (Note Taker). Skips greeting, auto-switches to split mode |
| `voice.tts_voice` | No | Voice name: `Aoede`, `Puck`, `Charon`, `Kore`, `Fenrir`. Falls back to `config.yaml` `split.tts_voice` |
| `voice.tts_style` | No | Speaking style: `extremely fast`, `whispering`, `shouting`, `sarcasm`, `robotic`. Falls back to `config.yaml` `split.tts_style` |
| `tools.builtin` | Yes | List of enabled tools (see below) |
| `tools.mcp_servers` | No | MCP server names from `config.yaml` to connect (e.g. `[redhat, jira]`) |
| `output.directory` | Yes | Where files are saved, relative to `~/Documents/voxcat/` |

#### Available built-in tools

| Tool | Purpose |
|---|---|
| `websearch` | Web search via Tavily (requires `TAVILY_API_KEY`) |
| `web_read` | Fetch and read web page content (requires `TAVILY_API_KEY`) |
| `file_read` | Read a file from persona output directory |
| `file_write` | Write a file (.md, .txt, .json, .yaml, .yml) |
| `file_list` | List files in persona output directory |
| `set_topic` | Set session topic (used in filenames) |
| `summarize_session` | Generate structured summary of conversation |
| `get_current_time` | Current date and time |
| `deep_analysis` | Extended thinking with Gemini 3.7 Flash |
| `research` | Multi-step research with extended thinking |
| `notebooklm_sync` | Sync document to Google NotebookLM (requires `NOTEBOOKLM_NOTEBOOK_ID`) |

#### Instruction body

Everything after the closing `---` is the system instruction. Write for voice — short sentences, no markdown, no URLs. The agent automatically gets common voice rules (no markdown in speech, natural numbers, barge-in handling) prepended to your instruction.

### config.yaml

Voice settings, tool model, MCP servers, default persona:

```yaml
voice:
  mode: "split"                             # or "live"
  split:
    tts_voice: "Aoede"                      # global default, per-persona overrides in persona files
    tts_style: "extremely fast"             # extremely fast, whispering, shouting, sarcasm, robotic

tools:
  analysis_model: "gemini-3.7-flash"
  thinking_budget: 8192

mcp_servers: {}                             # add your MCP servers here

persona:
  default: "thinking-partner"
```

## UI

Custom React client with the "Instrument Panel" design:

- **Top rail**: wordmark, persona label, voice instrument (6 states), mic controls, theme toggle
- **Timeline**: timestamped transcript with inline tool events, 4 result treatments (results list, prose, status, raw JSON)
- **Output tree**: collapsible per-persona folders + NotebookLM sources, rename/delete files
- **Document preview**: rendered markdown with GFM tables, RAW toggle
- **Past sessions**: browse, preview, rename, delete, continue with context injection
- **Real audio meter**: 32-bar visualizer driven by AnalyserNode on mic stream
- **Dark/light themes**: CSS custom property swap, persisted to localStorage

## Project structure

```
src/voxcat/
  cli.py            CLI entry point, HTTP routes, server startup
  bot.py            Pipeline orchestrator (live + split modes)
  tools.py          11 tool handlers + build_tools() registry
  personas.py       Persona file loader (YAML frontmatter + markdown)
  transcript.py     TranscriptRecorder (output + session files)
  mcp_connect.py    MCP server connection with read-only filter
  filestore.py      safe_resolve() for path traversal prevention
  personas/         Default persona files (copied by voxcat init)

client/src/
  App.tsx            Landing page, session view, past sessions
  components/
    VoiceInstrument  6-state ring + meter + status label
    ActivityPanel    Timeline with auto-scroll + TOOLS ONLY filter
    ToolResultCard   4 result treatments (results, prose, status, raw)
    OutputTree       Collapsible folders + NotebookLM group
    FilePreview      Markdown preview + RAW + rename/delete
    PersonaSelector  Landing page persona rows with descriptions
  hooks/
    useActivityLog   RTVI event subscription (transcript + tool events)
    useAudioLevel    AnalyserNode mic visualization
```

## Environment variables

All keys go in `~/.config/voxcat/.env` (created by `voxcat init`).

| Variable | Required | Purpose |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Yes | Gemini Live, Flash, TTS, Transcribe |
| `TAVILY_API_KEY` | No | Web search + web read tools |
| `NOTEBOOKLM_NOTEBOOK_ID` | No | Sync documents to NotebookLM |
| `RH_API_OFFLINE_TOKEN` | No | [redhat-api-mcp](https://github.com/judexzhu/redhat-api-mcp) server |
| `JIRA_SERVER_URL` | No | [mcp-jira](https://github.com/judexzhu/mcp-jira) server |
| `JIRA_API_TOKEN` | No | [mcp-jira](https://github.com/judexzhu/mcp-jira) server |
| `JIRA_USER_EMAIL` | No | [mcp-jira](https://github.com/judexzhu/mcp-jira) server |

## License

[AGPL-3.0](LICENSE) — free to use, modify, and distribute. If you run a modified version as a network service, you must open-source your changes.
