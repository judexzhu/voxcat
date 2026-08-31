# Voxcat User Manual

Version 0.1.0

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Installation](#2-installation)
3. [Starting Voxcat](#3-starting-voxcat)
4. [The Landing Page](#4-the-landing-page)
5. [The Session View](#5-the-session-view)
6. [Personas](#6-personas)
7. [Built-in Tools](#7-built-in-tools)
8. [Voice Modes](#8-voice-modes)
9. [Sessions and History](#9-sessions-and-history)
10. [Output Files](#10-output-files)
11. [MCP Integration](#11-mcp-integration)
12. [NotebookLM Integration](#12-notebooklm-integration)
13. [Configuration Reference](#13-configuration-reference)
14. [Architecture Overview](#14-architecture-overview)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Introduction

Voxcat is a voice-first AI agent that runs in your browser. You speak to it, and it speaks back. While you talk, it can search the web, write files, query external services, and produce structured markdown output, all driven by natural conversation.

What makes Voxcat different from a chatbot is the **persona system**. Before each session, you choose a role for the agent: a Thinking Partner that brainstorms with you, a Devil's Advocate that challenges your ideas, a Note Taker that silently transcribes, or an SRE Assistant that queries case management systems. Each persona has its own instruction set, its own tool access, and its own output folder. Everything the agent produces during a session is filed under that persona's directory.

Voxcat is built on [Pipecat](https://github.com/pipecat-ai/pipecat) for pipeline orchestration, Google Gemini for speech and language processing, and WebRTC for real-time audio transport. The frontend is a custom React application designed around the "Instrument Panel" visual language: monospace typography, zero border-radius, real-time audio visualization, and a dark/light theme system.

### What You Need

- A computer with a microphone
- A modern browser (Chrome, Firefox, Edge, Safari)
- Python 3.13 or later
- The `uv` package manager
- A Google API key with Gemini access

---

## 2. Installation

### Step 1: Install

```bash
uv tool install git+https://github.com/judexzhu/voxcat
```

This installs Voxcat as a standalone command. No clone, no Node.js, no build steps.

### Step 2: Initialize Configuration

```bash
voxcat init
```

This creates:
- `~/.config/voxcat/config.yaml` — persona, voice, and server settings
- `~/.config/voxcat/.env` — API keys

### Step 3: Configure API Keys

Edit `~/.config/voxcat/.env`:

```env
# Required
GOOGLE_API_KEY=your-google-api-key

# Optional: enables web_search, web_read, and research tools
TAVILY_API_KEY=your-tavily-api-key

# Optional: enables notebooklm_sync tool and NotebookLM source browsing
NOTEBOOKLM_NOTEBOOK_ID=your-notebook-id
```

**Required keys:**

- `GOOGLE_API_KEY` powers all voice and language processing (Gemini Live, Flash, Transcribe, TTS). Without it, Voxcat cannot start a session.

**Optional keys:**

- Without `TAVILY_API_KEY`, three tools are silently disabled: `web_search`, `web_read`, and `research`. The agent still works, but cannot search the web or read URLs.
- Without `NOTEBOOKLM_NOTEBOOK_ID`, the `notebooklm_sync` tool is disabled and the NotebookLM section does not appear in the Output panel.

### Step 4: Start

```bash
voxcat
```

Open `http://localhost:7860` in your browser.

### Updating

```bash
uv tool install --force git+https://github.com/judexzhu/voxcat
```

### File Locations

| Path | Purpose |
| --- | --- |
| `~/.config/voxcat/config.yaml` | Configuration |
| `~/.config/voxcat/.env` | API keys |
| `~/Documents/voxcat/output/` | Per-persona output files |
| `~/Documents/voxcat/sessions/` | Session transcripts |
| `~/Documents/voxcat/logs/` | Log files |

### Development Mode

For modifying the frontend or backend source:

```bash
git clone https://github.com/judexzhu/voxcat && cd voxcat
uv sync

# Terminal 1: frontend with hot reload (requires Node.js 20+)
cd client && npm ci && npm run dev

# Terminal 2: backend
uv run voxcat
```

In development mode, open `http://localhost:5173`. The Vite dev server proxies API calls to the backend on port 7860.

---

## 3. Starting Voxcat

Run:

```bash
voxcat
```

Open your browser to `http://localhost:7860`. You are taken to the Landing Page.

The server listens on `0.0.0.0:7860` by default. You can change the host and port in `~/.config/voxcat/config.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 7860
```

Command-line options:

```bash
voxcat --port 8080           # override port
voxcat --log-level DEBUG     # verbose logging
voxcat --config /path/to/config.yaml  # custom config path
```

---

## 4. The Landing Page

The landing page is split into two halves.

### Left Half

- **Headline**: "Think out loud. Keep the notes."
- **Spec rows**: three key-value pairs showing latency, available tools, and output format. These are static informational labels.

### Right Half: Persona Selector

A vertical list of all configured personas. Each row shows:

- **Dot indicator**: a small square, filled with the accent color when selected
- **Persona name**: displayed in Newsreader serif font (e.g., "Thinking Partner")
- **Description**: one-line summary of the persona's behavior
- **SELECTED label**: appears on the currently highlighted persona
- **File count**: shows the persona's output directory path and how many files exist in it (e.g., `thinking-partner/ . 12`)

Click a persona row to select it. Click **START SESSION** to begin.

The footer note "MICROPHONE REQUIRED" reminds you that browser mic access is needed.

### Header Bar

- **VOXCAT wordmark** (top left)
- **GEMINI LIVE . SMALLWEBRTC** label (top right, informational)
- **PAST SESSIONS** link (top right): switches to the session history view
- **Theme toggle** (top right): sun/moon icon button. Click to switch between dark and light themes. Your choice is saved to `localStorage` and persists across sessions and page reloads.

---

## 5. The Session View

After clicking START SESSION, the browser requests microphone access and establishes a WebRTC connection to the backend. Once connected, the session view appears.

### 5.1 The Top Rail

A thin horizontal bar (52px) at the top of the screen. It is divided into three sections:

**Left section:**
- VOXCAT wordmark
- Dot separator
- Current persona name (uppercase, e.g., THINKING-PARTNER)
- Dot separator
- Output directory path (e.g., `output/thinking-partner/`)

**Center section (the Voice Instrument):**

The voice instrument consists of three parts arranged horizontally:

1. **Ring**: a circular indicator (38px) that visually represents the current state:
   - **CONNECTING**: pulsing halo animation, small purple dot
   - **LISTENING**: breathing glow animation, bright purple dot with box shadow
   - **SPEAKING**: larger dot, faster breathing, filled halo backdrop
   - **MUTED**: static ring outline with a diagonal slash through the center
   - **WORKING**: dot with fast breathing, static ring
   - **ENDED**: static ring with horizontal dash

2. **Meter**: depends on state:
   - **CONNECTING**: a sweep bar animation (a thin line with a moving highlight segment)
   - **LISTENING / SPEAKING**: 32-bar audio level visualizer. When the mic is active, these bars respond in real time to your microphone input via the browser's AnalyserNode API. The bars show actual frequency data (FFT size 64, smoothing constant 0.7). When muted, bars freeze at minimum height
   - **WORKING**: displays the tool name (e.g., "WEB_SEARCH") with a sweep bar
   - **ENDED**: nothing displayed

3. **Status label**: two lines of text:
   - Top line: state name (CONNECTING, LISTENING, SPEAKING, MUTED, WORKING, SESSION ENDED)
   - Bottom line: contextual info:
     - CONNECTING: "NEGOTIATING WEBRTC"
     - LISTENING/SPEAKING: elapsed time (e.g., "03:42 ELAPSED")
     - MUTED: "MIC OFF . SESSION LIVE"
     - WORKING: "TOOL CALL IN FLIGHT"
     - ENDED: elapsed time and save path (e.g., "03:42 . TRANSCRIPT SAVED TO output/thinking-partner/")

**Right section:**
- **Theme toggle**: same sun/moon button as on the landing page
- **Mic indicator**: a small dot (green when mic is on, gray when off, pulsing purple when syncing) with label text (MIC ON / MIC OFF / SYNCING)
- **MUTE / UNMUTE button**: toggles the microphone
  - Muting is immediate: one click, mic goes off
  - Unmuting shows "SYNCING" for approximately one second while the microphone reconnects to the WebRTC transport. The button is disabled during syncing to prevent double-clicks
- **END button**: disconnects the session. After ending, the button changes to "NEW SESSION" which reloads the page

### 5.2 The Three-Column Body

Below the rail, the screen is divided into three resizable columns separated by draggable dividers. Hover over a divider to see it highlight in the accent color; drag to resize.

Default column proportions: 38% / 22% / 40%. Each column has a minimum width (20% / 12% / 20%).

#### Column 1: Activity Timeline

The left column shows a live, chronological feed of everything that happens in the session.

**Panel header:**
- Label: "TIMELINE"
- Event count (e.g., "47 EVENTS")
- **TOOLS ONLY** toggle: when active (highlighted in accent color), filters the timeline to show only tool-start and tool-result events. All user and bot speech entries are hidden. Click again to show everything.

**Timeline entries:**

Each entry has a timestamp in the left gutter (HH:MM:SS format, 68px wide) and content on the right.

Four entry types:

1. **User speech** (kind: `user`)
   - Speaker label: "YOU" in muted text
   - Your transcribed speech in Newsreader serif, 17px

2. **Bot speech** (kind: `bot`)
   - Speaker label: "VOXCAT" in accent color
   - The bot's text response in Newsreader serif, 17px
   - If the bot is currently speaking (in split mode, text arrives before audio finishes), a **sweep bar** animation appears below the text. This thin animated line indicates audio is still playing. It disappears when the bot finishes speaking.

3. **Tool start** (kind: `tool-start`)
   - Displayed with a tinted background row
   - Small filled square (accent color) followed by the tool name in uppercase (e.g., "WEB_SEARCH")

4. **Tool result** (kind: `tool-result`)
   - Displayed with a tinted background row
   - Rendered by the ToolResultCard component, which classifies results into one of four treatments:

   **Results list** (for `results`, `files`, or `issues` arrays):
   - Each result shows a title (clickable for files), a content snippet (first 200 characters), and a source URL (clickable, opens in new tab)
   - File names in results are clickable and open in the Document Preview panel
   - Header shows count (e.g., "5 RESULTS", "3 FILES", "2 ISSUES")

   **Prose result** (for `analysis`, `report`, or `content` fields):
   - Rendered as markdown with a left accent border
   - Used by deep_analysis, research, and content-heavy tool responses

   **Status result** (for `status`, `error`, or cancelled calls):
   - Single-line display with a colored chip
   - OK: green chip, shows the saved file path (clickable to open in preview)
   - DENIED: red chip, shows the error message
   - CANCELLED: muted chip, shown when a tool call is interrupted

   **Raw JSON** (fallback for unrecognized result shapes):
   - Displayed in a scrollable monospace box (max height 150px)
   - COPY button in the header copies the JSON to clipboard

   All tool results show **latency** (e.g., "1.2s" or "340ms") when available, calculated from the time between tool-start and tool-result events.

**Auto-scroll behavior:**

The timeline auto-scrolls to the latest entry as new events arrive. If you manually scroll upward (more than 60px from the bottom), auto-scroll pauses so you can read earlier entries without being pulled away. Scrolling back to the bottom re-enables auto-scroll.

#### Column 2: Output Tree

The center column shows all files organized by persona, plus NotebookLM sources if configured.

**Panel header:**
- Label: "OUTPUT"
- Refresh button (circular arrow)

**Folder groups:**

Each persona that has an output directory configured appears as a collapsible group:

- **Group header**: persona name in uppercase (e.g., "THINKING-PARTNER") with a chevron (triangular arrow) and file count on the right
- Click the header to collapse/expand the group
- When collapsed, only the header is visible with a "right-pointing" chevron
- When expanded, files are listed below with a "down-pointing" chevron

**File entries:**

- Displayed indented below the folder header
- Click a file to select it and view it in the Document Preview panel
- The selected file shows an accent-colored left border and tinted background
- Files are sorted by modification time (most recent first)
- Long file names are truncated with ellipsis

**NotebookLM group:**

If `NOTEBOOKLM_NOTEBOOK_ID` is set, a "NOTEBOOKLM" group appears at the bottom. It lists all sources in the configured notebook. Clicking a source loads its full text content in the Document Preview panel (read-only, no rename/delete).

**Footer:**

A summary line at the bottom: `N FILES . N ROOTS` (where ROOTS is the number of persona folders). If NotebookLM sources exist, appends `. N NLM`.

**Auto-refresh:**

The output tree refreshes automatically when the agent writes a file using the `file_write` tool. You do not need to manually refresh. The refresh is triggered by counting tool-result events with `functionName === "file_write"` in the activity log.

You can also manually refresh by clicking the refresh button in the panel header.

#### Column 3: Document Preview

The right column renders the content of the selected file.

**When no file is selected:**
- Shows centered italic text: "Select a file to preview"

**When a file is selected:**

**Panel header:**
- **Filename** (uppercase, clickable): click to enter rename mode
- **DELETE** button: two-click confirmation. First click changes text to "CONFIRM?" (in red). If you click again within 3 seconds, the file is deleted. If you wait, it reverts to "DELETE". After deletion, the preview clears and the output tree refreshes
- **RAW** toggle: switches between rendered markdown and raw plain text. When active, highlighted in accent color

**Rename:**

Click the filename in the header to enter rename mode. An inline text input appears with the current filename (minus extension). Press Enter to confirm (the `.md` or `.txt` extension is preserved automatically). Press Escape or click outside to cancel.

**Markdown rendering:**

Files are rendered as formatted markdown with full GFM (GitHub Flavored Markdown) support:

- **Headings**: H1 in Newsreader serif 28px; H2-H6 in monospace uppercase with accent coloring
- **Body text**: Newsreader serif 16px with 1.7 line height
- **Lists**: unordered lists use small filled squares as bullets; ordered lists use zero-padded numbers (01, 02, ...)
- **Code blocks**: monospace with a surface-colored background and subtle border
- **Inline code**: accent-colored text
- **Tables**: full GFM table support with border styling (requires the `remark-gfm` plugin)
- **Blockquotes**: left accent border, italic text
- **Links**: accent-colored with underline on hover
- **Horizontal rules**: thin separator lines

**NotebookLM source preview:**

When viewing a NotebookLM source (identified by the `__nlm__` persona key), the preview is read-only. The DELETE and rename controls are hidden. The content is fetched from the NotebookLM API and rendered as markdown.

**Auto-refresh:**

When the agent writes to the file you are currently viewing, the preview refreshes automatically. This uses the same `fileWriteCount` mechanism as the Output Tree.

---

## 6. Personas

A persona defines how the agent behaves during a session. Each persona has:

- **Instruction**: a system prompt that shapes the agent's personality and behavior
- **Tool access**: which built-in tools and MCP servers the persona can use
- **Output directory**: where files created during the session are stored
- **Silent mode** (optional): disables voice output, making the agent listen-only

### Common Instructions

All personas share a set of **common instructions** that are appended to the persona-specific instruction. These handle universal behaviors:

- Announce tool calls with a brief phrase before executing ("Let me check", "Looking that up")
- Never call the same tool twice with the same arguments
- Always speak tool results before calling another tool
- Map natural language to tool calls:
  - "Why" / "root cause" / "analyze" / "compare" triggers `deep_analysis`
  - "Research" / "look into" triggers `research`
  - Factual questions trigger `web_search`
  - "Wrap up" / "summarize" / "done" triggers `summarize_session`
  - "Sync to notebook" / "archive this" triggers `notebooklm_sync`
  - Time questions trigger `get_current_time`

### Thinking Partner (default)

**Slug:** `thinking-partner`

A brainstorming partner. Responds in 2-3 sentences max. Asks clarifying questions. Challenges assumptions constructively. Suggests connections between ideas. When you seem stuck, offers a different angle.

Has access to all 10 built-in tools. No MCP servers.

**Output directory:** `output/thinking-partner/`

### Devil's Advocate

**Slug:** `devils-advocate`

Takes the opposite side of whatever you say. Challenges every idea. Finds weaknesses. Pushes back hard but constructively. Always explains why something might be wrong. Never agrees just to be nice.

Has access to all 10 built-in tools. No MCP servers.

**Output directory:** `output/devils-advocate/`

### Note Taker

**Slug:** `note-taker`

**Silent mode enabled.** This persona does not speak unless directly asked ("read back", "what do you have"). It listens to everything you say and organizes it into structured notes with bullet points grouped by topic.

Key behaviors:
- Does not respond to the user unless directly asked a question
- Periodically saves notes using `file_write` without being asked (every 2-3 minutes or when a topic changes)
- Flags ambiguity with inline markers like `(Ambiguity: unclear term)`
- When asked to read back, speaks the organized notes

Silent mode only works in **split voice mode**. In live mode, the model always generates audio output regardless of the persona instruction. If you use the Note Taker persona, make sure `voice.mode` is set to `"split"` in `config.yaml`.

Has access to all 10 built-in tools. No MCP servers.

**Output directory:** `output/note-taker/`

### SRE Assistant

**Slug:** `sre`

A Platform SRE voice assistant. Extremely concise (1-2 sentences max). Evidence-first: never speculates. Names the tool it is calling before executing.

Understands domain-specific commands:
- Mentioning a case number triggers `get_case`
- "Search cases" or describing a problem triggers `search_cases` or `search_kcs`
- Mentioning a Jira ticket triggers `jira_get_issue`
- "Search Jira" triggers `jira_search_issues` with JQL
- When saving, uses a structured case report format

Has access to all 10 built-in tools plus the `redhat` and `jira` MCP servers.

**Output directory:** `output/sre/`

### Creating a Custom Persona

Add a new entry under `persona.profiles` in `config.yaml`:

```yaml
persona:
  profiles:
    my-persona:
      instruction: |
        You are a [role]. [Behavioral instructions here.]
        Keep responses [length guideline].
      tools:
        builtin:
          - websearch
          - web_read
          - file_read
          - file_write
          - file_list
          - summarize_session
          - get_current_time
          - deep_analysis
          - research
          - notebooklm_sync
        mcp_servers: []
      output:
        directory: "output/my-persona"
```

If you want a silent (listen-only) persona, add `silent: true` at the persona level:

```yaml
    my-listener:
      silent: true
      instruction: |
        ...
```

After editing `config.yaml`, restart Voxcat for changes to take effect.

The persona will automatically appear on the landing page. The `PersonaSelector` component reads persona names from the `/api/personas` endpoint, which returns whatever is configured in `config.yaml`.

Display names and descriptions for custom personas default to the slug name. To add custom display names and descriptions, you would modify the `PERSONA_LABELS` and `PERSONA_DESCS` maps in `client/src/components/PersonaSelector.tsx`.

---

## 7. Built-in Tools

Voxcat has 10 built-in tools. Each persona can enable a subset of these in its `tools.builtin` list. If a required API key is missing, the tool is silently skipped during registration (a warning is logged to the terminal).

### web_search

**Requires:** `TAVILY_API_KEY`

Searches the web using the Tavily API. Returns the top 5 results with title, URL, and a 500-character content snippet for each.

**How to trigger:** Ask a factual question, or say "search for..." The common instruction maps factual questions to this tool automatically.

**Example:** "What's the latest Kubernetes release?" The agent says "Let me check" and calls `web_search` with the query. Results appear in the timeline as a results list with clickable URLs.

### web_read

**Requires:** `TAVILY_API_KEY`

Extracts the full text content of a web page given its URL. Uses Tavily's extract API. Returns up to 5000 characters.

**How to trigger:** When search results contain a useful URL, ask the agent to read it. Or say "read this page" and provide a URL.

**Example:** After a web search returns results, the agent may automatically follow up by reading the most relevant URL.

### file_read

Reads a file from the current persona's output directory. Returns up to 5000 characters. The filename is resolved safely: path traversal attempts (e.g., `../../etc/passwd`) are blocked by the `safe_resolve()` function, which ensures the resolved path stays within the output directory.

**How to trigger:** "Read the file [name]" or "What's in [name]?"

### file_write

Writes content to a file in the current persona's output directory. Creates the file if it doesn't exist, overwrites if it does. Parent directories are created automatically.

**How to trigger:** "Save this", "Write that down", "Create a file called..." The common instruction tells the agent to save without asking for confirmation.

**Side effects in the UI:** When a `file_write` tool result arrives, the Output Tree and Document Preview automatically refresh without user action.

### file_list

Lists all files in the current persona's output directory, sorted by modification time (newest first). Returns up to 20 files with name and size.

**How to trigger:** "What files do I have?" or "List my files."

### deep_analysis

Sends a question to Gemini 3.7 Flash with extended thinking enabled (8192 token thinking budget). Returns up to 5000 characters of analysis. Use this for complex reasoning, root cause analysis, comparing trade-offs, or questions that need thorough multi-step thinking.

**How to trigger:** Questions containing "why", "root cause", "analyze", "compare", or "trade-offs" automatically trigger this tool. You can also say "think deeper" or "analyze this" to invoke it explicitly.

**Context parameter:** The agent can include supporting context (case details, logs, error messages) alongside the question for more informed analysis.

### research

**Requires:** `TAVILY_API_KEY`

Performs multi-step research on a topic:

1. Searches the web for the topic (5 results)
2. Extracts full page content from the top 3 URLs (up to 3000 characters each)
3. Sends all gathered information to Gemini 3.7 Flash with extended thinking
4. Returns a structured report with: Key Findings, Details, Sources, and Open Questions

This tool takes 10-15 seconds to complete because of the multi-step process.

**How to trigger:** "Research [topic]" or "Look into [topic]."

### summarize_session

Retrieves the current session transcript and instructs the agent to summarize it into four sections: Key Ideas, Decisions Made, Action Items, and Open Questions. The transcript includes all user and bot turns with timestamps.

**How to trigger:** "Wrap up", "Summarize", or "Done."

### get_current_time

Returns the current date and time in both ISO format and human-readable format (e.g., "Friday, August 29, 2026 at 11:30 AM").

**How to trigger:** "What time is it?" or "What's today's date?"

### notebooklm_sync

**Requires:** `NOTEBOOKLM_NOTEBOOK_ID`

Pushes content to Google NotebookLM as a text source in the configured notebook. The content appears as a source document in NotebookLM that can be queried, summarized, and used for audio overviews.

**How to trigger:** "Sync to notebook", "Push to NotebookLM", or "Archive this."

Authentication uses cookie-based storage via the `notebooklm-py` library. You need to authenticate once via the NotebookLM web interface and export cookies for the library to use.

---

## 8. Voice Modes

Voxcat supports two voice processing architectures. Set the mode in `config.yaml` under `voice.mode`.

### Live Mode

```yaml
voice:
  mode: "live"
  name: "Aoede"
  live_model: "gemini-3.1-flash-live-preview"
```

**Pipeline:**

```
Microphone -> Gemini 3.1 Flash Live (STT + LLM + TTS) -> Speaker
```

A single Gemini Live model handles everything: speech recognition, reasoning, and speech synthesis in one round trip.

**Characteristics:**
- Lowest latency (~300ms speech-to-speech)
- Natural conversational flow with interruption support
- Less capable at complex tool calls and multi-step reasoning
- Cannot be made silent (live mode always generates audio)
- The voice is set by the `voice.name` field

**Available voices for live mode:** Puck, Charon, Kore, Fenrir, Aoede

### Split Mode

```yaml
voice:
  mode: "split"
  split:
    stt_model: "gemini-3.5-transcribe-live"
    llm_model: "gemini-3.7-flash"
    tts_model: "gemini-3.1-flash-tts-preview"
    tts_voice: "Aoede"
```

**Pipeline:**

```
Microphone -> Gemini 3.5 Transcribe Live (STT)
           -> Gemini 3.7 Flash (LLM + tool calls)
           -> TTSStyleProcessor (optional style tag)
           -> Gemini 3.1 Flash TTS (text-to-speech)
           -> Speaker
```

Three separate models handle each stage independently.

**Characteristics:**
- Higher latency (~800ms speech-to-speech)
- Significantly better at reasoning, tool use, and following complex instructions
- Supports silent mode (the Note Taker persona skips the TTS stage entirely)
- Text appears in the timeline before audio finishes (the "read-ahead" effect) because `BotLlmText` events arrive as the LLM generates text, before TTS processes it
- Each model can be individually configured and upgraded
- The voice is set by `split.tts_voice`

**TTS style control:**

The `tts_style` option prepends a Gemini TTS style tag to the start of each response. Available styles:

| Style | Effect |
| --- | --- |
| `extremely fast` | Speeds up speech, ideal for fast-paced dialogue |
| `whispering` | Quiet, whispering delivery |
| `shouting` | Loud, shouting delivery |
| `sarcasm` | Sarcastic tone |
| `robotic` | Robotic voice |

Omit the field for default delivery. Style tags affect all subsequent speech in the response.

### Choosing Between Modes

| Aspect | Live | Split |
| --- | --- | --- |
| Latency | ~300ms | ~800ms |
| Reasoning quality | Good | Better |
| Tool call reliability | Adequate | Superior |
| Silent mode support | No | Yes |
| Read-ahead text | No | Yes |
| Per-layer model choice | No | Yes |
| Cost | Single model | Three models |

For most use cases, **split mode** provides a better experience despite the higher latency. Live mode is best when sub-second response time matters more than reasoning depth.

---

## 9. Sessions and History

### Automatic Session Recording

Every session is recorded automatically. When you disconnect (click END or close the browser), two files are saved:

1. **Transcript**: saved to the persona's output directory (e.g., `output/thinking-partner/2026-08-29-untitled.md`). Contains a structured template (Key Ideas, Decisions Made, Action Items, Open Questions) followed by the raw transcript with timestamps.

2. **Session file**: saved to `sessions/<persona>/` (e.g., `sessions/thinking-partner/2026-08-29_143025.md`). This is what appears in the Past Sessions browser.

### Browsing Past Sessions

Click **PAST SESSIONS** on the landing page header. The view shows two resizable panels:

**Left panel: Session List**
- All past sessions across all personas, sorted by most recent first
- Each entry shows the persona name (uppercase) and the filename
- Header shows total count (e.g., "12 SESSIONS")

**Right panel: Session Preview**
- Renders the selected session's content as markdown
- Shows a preview of the full conversation transcript

**Actions on a selected session:**

- **CONTINUE SESSION**: starts a new session with the same persona, injecting the entire transcript as prior context. The agent greets you back and references what was discussed. See "Continuing a Session" below.
- **Rename**: click the filename to enter inline edit mode. Press Enter to save, Escape to cancel.
- **DELETE**: two-click confirmation. First click shows "CONFIRM?" in red. Click again to delete. Auto-reverts after 3 seconds if you don't confirm.

Click **NEW SESSION** in the header to go back to the persona selector.

### Continuing a Session

When you click CONTINUE SESSION on a past session, the following happens:

1. The past session's full transcript is loaded as the `context` parameter
2. A new WebRTC connection starts with the same persona
3. The transcript is injected as a `developer` message in the LLM context:

   > "The user is continuing a previous session. Here is the transcript: [full transcript]. Welcome them back briefly. Reference what was discussed. Ask what they'd like to continue with."

4. The agent greets you referencing the previous conversation

**Continuation appends, not forks.** The new conversation turns are appended to the same session file, separated by a `---` divider with a timestamp header:

```markdown
[original session content]

---

**Continued:** 2026-08-29 15:30  |  **Duration:** 12m

**[15:30:45] User:** Let's pick up where we left off...

**[15:30:48] Assistant:** Welcome back! Last time we discussed...
```

This means your session history grows as a single continuous document, not a tree of forks.

---

## 10. Output Files

Each persona writes files to its own output directory:

```
output/
  thinking-partner/
    2026-08-29-brainstorm-cloud-migration.md
    2026-08-29-untitled.md
  devils-advocate/
    2026-08-29-pricing-strategy-critique.md
  note-taker/
    meeting-notes-standup.md
  sre/
    case-12345-analysis.md
```

Files are created by the `file_write` tool during sessions. The agent names files based on the topic of conversation. File format is markdown.

### File Management in the UI

**In the Output Tree (column 2):**
- Click a file to preview it
- Files are sorted by modification time (newest first)
- Groups collapse/expand by clicking the folder header

**In the Document Preview (column 3):**
- **Rename**: click the filename in the header, edit inline, press Enter
- **Delete**: click DELETE, then click CONFIRM within 3 seconds
- **RAW toggle**: switch between rendered markdown and raw text
- **Auto-refresh**: if the agent writes to the file you are viewing, the content updates live

### File Management via the API

The backend exposes REST endpoints for file operations:

- `GET /api/files/tree` — returns all files organized by persona
- `GET /api/files/{filename}?persona=X` — read file content (max 10,000 characters)
- `DELETE /api/files/{filename}?persona=X` — delete a file
- `POST /api/files/{filename}/rename?persona=X&new_name=Y` — rename a file

All file paths are validated by `safe_resolve()` to prevent path traversal. A filename like `../../etc/passwd` resolves to `None` and returns an error.

---

## 11. MCP Integration

Voxcat can connect to external [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) servers, giving personas access to tools beyond the built-in set. MCP servers are separate processes that Voxcat starts and communicates with via stdin/stdout.

### How It Works

1. When a session starts and the selected persona has `mcp_servers` listed, Voxcat reads the MCP server definitions from `config.yaml`
2. For each server, it checks that all required environment variables are present. Missing vars cause the server to be skipped with a warning
3. It starts the server process using `StdioServerParameters` (command, args, env, cwd)
4. It filters the server's available tools to only those listed in `read_only_tools` (an allowlist)
5. The filtered tools are registered alongside the built-in tools
6. When the session ends, all MCP client connections are closed

### Configuration

Each MCP server is defined under `mcp_servers` in `config.yaml`:

```yaml
mcp_servers:
  server-name:
    command: "uv"
    args: ["run", "python", "-m", "my_mcp_server.server"]
    cwd: "/absolute/path/to/server/repo"
    env_keys: [API_TOKEN, API_URL]
    read_only_tools:
      - search_items
      - get_item
```

**Fields:**

| Field | Type | Description |
| --- | --- | --- |
| `command` | string | The executable to run (e.g., `"uv"`, `"node"`, `"python"`) |
| `args` | list | Command-line arguments passed to the executable |
| `cwd` | string | Working directory for the server process. Use absolute paths |
| `env_keys` | list | Environment variable names to forward from your `.env` file. Only these variables (plus `PATH`) are passed to the server process |
| `read_only_tools` | list | Allowlist of tool names to expose. Tools not in this list are filtered out even if the server offers them. This is a safety mechanism to prevent unintended write operations |

### Assigning MCP Servers to Personas

In each persona's `tools` section, list the server names:

```yaml
persona:
  profiles:
    my-persona:
      tools:
        builtin: [...]
        mcp_servers: [server-name, another-server]
```

Only personas that list a server will have access to its tools. Other personas see only built-in tools.

### Pre-Configured MCP Servers

Voxcat ships with two MCP server configurations for the SRE persona:

**Red Hat API (`redhat`):**
- Provides: `search_cases`, `get_case`, `search_kcs`, `get_kcs`, `search_docs`, `get_doc`, `search_cve`, `get_cve`
- Requires: `RH_API_OFFLINE_TOKEN`

**Jira (`jira`):**
- Provides: `jira_search_issues`, `jira_get_issue`, `jira_get_create_meta`
- Requires: `JIRA_SERVER_URL`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL`

### Adding Your Own MCP Server

1. Define the server under `mcp_servers` in `config.yaml`
2. Add the server name to the desired persona's `mcp_servers` list
3. Set any required environment variables in `.env`
4. Restart Voxcat

The server must implement the MCP protocol over stdin/stdout. Any MCP-compatible server works. Check the server's documentation for the available tool names to use in `read_only_tools`.

---

## 12. NotebookLM Integration

Voxcat integrates with Google NotebookLM in two ways:

### Syncing Content to NotebookLM

The `notebooklm_sync` tool pushes text content to a NotebookLM notebook as a source document. This lets you archive session summaries, research reports, or case analyses directly into your knowledge base.

**Setup:**
1. Set `NOTEBOOKLM_NOTEBOOK_ID` in `.env` to the ID of your target notebook
2. Authenticate with NotebookLM using cookie-based storage (see the `notebooklm-py` library documentation)

**Usage:** Say "sync to notebook" or "archive this" during a session. The agent creates a source document with a title and content in your notebook.

### Browsing NotebookLM Sources

When `NOTEBOOKLM_NOTEBOOK_ID` is configured, the Output Tree (column 2) shows a "NOTEBOOKLM" group at the bottom. This group lists all source documents in your notebook.

Click any source to preview its full text content in the Document Preview panel (column 3). NotebookLM sources are read-only in the UI: rename and delete controls are hidden.

**API endpoints:**
- `GET /api/notebooklm/sources` — lists all sources in the configured notebook
- `GET /api/notebooklm/sources/{source_id}` — returns the full text content of a source (up to 20,000 characters, in markdown format)

---

## 13. Configuration Reference

All configuration lives in `config.yaml` in the project root.

### voice

Controls the voice processing pipeline.

```yaml
voice:
  name: "Aoede"
  mode: "split"
  live_model: "gemini-3.1-flash-live-preview"
  split:
    stt_engine: "gemini"
    stt_model: "gemini-3.5-transcribe-live"
    whisper_model: "mlx-community/whisper-large-v3-turbo"
    llm_model: "gemini-3.7-flash"
    tts_model: "gemini-3.1-flash-tts-preview"
    tts_voice: "Kore"
    tts_pace: "fast"
```

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | string | `"Aoede"` | Default voice for live mode. Options: Puck, Charon, Kore, Fenrir, Aoede |
| `mode` | string | `"live"` | Pipeline architecture: `"live"` (single model) or `"split"` (three models) |
| `live_model` | string | `"gemini-3.1-flash-live-preview"` | Model for live mode (handles STT+LLM+TTS) |
| `split.stt_model` | string | `"gemini-3.5-transcribe-live"` | Speech-to-text model for split mode |
| `split.llm_model` | string | `"gemini-3.7-flash"` | Language model for split mode (reasoning + tool calls) |
| `split.tts_model` | string | `"gemini-3.1-flash-tts-preview"` | Text-to-speech model for split mode |
| `split.tts_voice` | string | falls back to `name` | Voice for split mode TTS. Overrides `voice.name` |
| `split.tts_style` | string | none | TTS style tag: `"extremely fast"`, `"whispering"`, `"shouting"`, `"sarcasm"`, `"robotic"`, or omit for default |

### mcp_servers

MCP server definitions. See [MCP Integration](#11-mcp-integration) for details.

```yaml
mcp_servers:
  server-name:
    command: string        # executable to run
    args: [string]         # command-line arguments
    cwd: string            # working directory (absolute path)
    env_keys: [string]     # env var names to forward from .env
    read_only_tools:       # tool allowlist
      - tool_name
```

### persona

Controls persona definitions and shared behavior.

```yaml
persona:
  default: "thinking-partner"
  common_instruction: |
    Shared instructions for all personas...
  profiles:
    persona-slug:
      instruction: |
        Persona-specific instructions...
      silent: false
      tools:
        builtin:
          - tool_name
        mcp_servers:
          - server_name
      output:
        directory: "output/persona-slug"
```

| Field | Type | Description |
| --- | --- | --- |
| `default` | string | Persona slug used when none is specified |
| `common_instruction` | string | Instructions appended to every persona's instruction |
| `profiles` | map | Persona definitions keyed by slug |
| `profiles.<slug>.instruction` | string | System prompt for this persona |
| `profiles.<slug>.silent` | boolean | If `true`, skips TTS output (split mode only) |
| `profiles.<slug>.tools.builtin` | list | Built-in tool names to enable |
| `profiles.<slug>.tools.mcp_servers` | list | MCP server names this persona can access |
| `profiles.<slug>.output.directory` | string | File output path relative to project root |

**Built-in tool names for the `builtin` list:**
`websearch`, `web_read`, `file_read`, `file_write`, `file_list`, `summarize_session`, `get_current_time`, `deep_analysis`, `research`, `notebooklm_sync`

### server

```yaml
server:
  host: "0.0.0.0"
  port: 7860
```

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `host` | string | `"0.0.0.0"` | Bind address |
| `port` | integer | `7860` | HTTP server port |

---

## 14. Architecture Overview

This section describes how the pieces fit together for users who want to understand the system or extend it.

### Backend

The backend is a single Python process (`bot.py`) that serves three roles:

1. **HTTP server** (FastAPI + Uvicorn): serves the static frontend, REST API endpoints for file/session/persona management, and the WebRTC signaling endpoint (`/start`)
2. **Pipeline orchestrator**: for each WebRTC connection, creates a Pipecat pipeline with the selected voice mode (live or split), registers tools, and manages the session lifecycle
3. **Transcript recorder**: records all user and assistant turns with timestamps, saves transcripts and session files on disconnect

**Key modules:**

| File | Purpose |
| --- | --- |
| `bot.py` | Pipeline setup, HTTP routes, entry point |
| `tools.py` | 10 tool handlers + `build_tools()` registry |
| `transcript.py` | `TranscriptRecorder` class for saving transcripts and sessions |
| `mcp_connect.py` | MCP server connection with `tools_filter` for allowlisting |
| `filestore.py` | `safe_resolve()` path traversal prevention |
| `config.yaml` | All configuration |

### Frontend

A React 18 application built with Vite, using:

- `@pipecat-ai/client-react` + `@pipecat-ai/small-webrtc-transport` for WebRTC connection and RTVI event handling
- `react-resizable-panels` for draggable column dividers
- `react-markdown` + `remark-gfm` for markdown rendering
- Web Audio API (`AnalyserNode`) for real-time mic visualization
- CSS custom properties for dark/light theming

**Component hierarchy:**

```
App
  LandingPage
    PersonaSelector
    PastSessions
  SessionPage
    PipecatAppBase (WebRTC connection)
      SessionView
        VoiceInstrument (ring + meter + status)
        ActivityPanel (timeline)
          ToolResultCard (4 result treatments)
        OutputTree (file explorer + NotebookLM)
        FilePreview (markdown viewer + rename/delete)
```

### Data Flow

```
Browser mic audio
  -> WebRTC transport
  -> Pipecat pipeline (STT -> LLM -> TTS)
  -> WebRTC transport
  -> Browser speaker

RTVI data channel (parallel):
  UserTranscript events    -> useActivityLog hook -> ActivityPanel
  BotLlmText events        -> useActivityLog hook -> ActivityPanel (read-ahead text)
  BotTtsText events        -> speaking state      -> sweep bar indicator
  BotStoppedSpeaking       -> reset speaking      -> sweep bar removed
  LLMFunctionCallStarted   -> useActivityLog hook -> ToolResultCard (tool-start)
  LLMFunctionCallStopped   -> useActivityLog hook -> ToolResultCard (tool-result)

file_write tool result -> fileWriteCount state -> OutputTree refresh + FilePreview refresh
```

### Large Result Handling

When a tool returns more than 5000 characters of JSON (common with MCP tools like Jira or Red Hat case search), the `ResultSpillProcessor` in the pipeline automatically:

1. Saves the full result to `output/<persona>/tool-results/<tool>-<timestamp>.json`
2. Replaces the LLM context with a 2000-character preview plus the file path
3. Instructs the agent to use `file_read` if it needs the full data

This prevents large tool results from consuming the LLM's context window and degrading response quality. The full data is preserved on disk and accessible on demand. The UI timeline still shows the complete result via the RTVI data channel.

### Security

- **Path traversal prevention**: all file operations go through `safe_resolve()`, which resolves the path and checks that it stays within the allowed base directory
- **MCP tool allowlisting**: `read_only_tools` filters MCP server tools to only those explicitly listed
- **Environment variable isolation**: MCP server processes only receive the environment variables listed in `env_keys` plus `PATH`
- **No authentication**: Voxcat is designed for local use. There is no login system. Do not expose it on a public network without adding authentication.

---

## 15. Troubleshooting

### Blank page at localhost:7860

The frontend assets are not built or not found. Check that `client/dist/` exists and contains files. If not, run:

```bash
cd client && npm ci && npm run build
```

Or run `./setup.sh` which handles this automatically if Node.js is available.

### No voice output from the agent

1. Check that your browser allows audio playback (some browsers require a user gesture before playing audio)
2. Check the terminal logs for errors. Look for connection failures or API key issues
3. If using the Note Taker persona, this is expected behavior (silent mode)

### Microphone not working

1. When the browser prompts for microphone access, click "Allow"
2. Check that the audio meter in the top rail shows bar activity when you speak
3. If the meter stays flat, your browser may not have mic access. Check browser settings under Site Settings > Microphone
4. Ensure no other application has exclusive mic access

### Mute/Unmute behavior

- **Muting** is immediate: one click, mic goes off
- **Unmuting** shows "SYNCING" for about one second while the mic reconnects to the WebRTC transport. This brief delay is by design. The button is disabled during syncing

### Tool calls fail or the agent says "I can't do that"

1. Check that the required API keys are set in `.env`:
   - `TAVILY_API_KEY` for web_search, web_read, research
   - `NOTEBOOKLM_NOTEBOOK_ID` for notebooklm_sync
2. Check the terminal logs. Missing keys produce warnings like: `Tool not available: websearch (missing API key or not implemented)`
3. Make sure the tool is listed in the persona's `tools.builtin` array in `config.yaml`

### MCP server won't connect

1. Verify the `cwd` path exists and contains the server code
2. Try running the server manually: `cd /path/to/server && uv run python -m server_module.server`
3. Check that all `env_keys` variables are set in `.env`
4. Check terminal logs for: `MCP server X skipped: missing env vars [...]` or `MCP server X failed to connect: ...`

### Note Taker still speaks

The Note Taker's silent mode only works in **split** voice mode. In live mode, the Gemini Live model always generates audio output regardless of instructions. Set:

```yaml
voice:
  mode: "split"
```

### Timeline stops auto-scrolling

If you scrolled up to read earlier entries, auto-scroll pauses. Scroll back to the bottom of the timeline (within 60px) to re-enable it.

### Theme toggle resets after session ends

Theme choice is stored in `localStorage` under the key `voxcat-theme`. If your browser clears localStorage on close, the theme will reset to dark (default). This is a browser setting, not a Voxcat issue.

### File rename doesn't add an extension

File extensions (`.md` or `.txt`) are preserved automatically. If the original file is `notes.md` and you rename to `meeting-notes`, it becomes `meeting-notes.md`. The server-side rename handler adds `.md` if no recognized extension is present.

### Agent repeats the same tool call

The common instruction tells the agent never to call the same tool twice with the same arguments. If this happens, it is a model behavior issue. Mentioning "you already searched for that" usually corrects it mid-session.
