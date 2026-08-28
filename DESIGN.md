# Voxcat — Design Document

**Product**: Voice AI agent with swappable personas. Same pipeline (Voice → Agent → Tools → Output), different roles via persona profiles.

## Architecture

- **Transport**: SmallWebRTC (browser-based, self-hosted, dev/prod parity)
- **Model**: Gemini Live (native speech-to-speech, ~300ms latency, long-term choice)
- **Tools**: Function calling via Pipecat's FunctionSchema pattern
- **Output**: Local files, scoped per-persona output directory

## Persona System

Persona is a **profile**, not just a system instruction. Each profile binds:
- System instruction (role behavior)
- Built-in tool set (websearch, file ops)
- MCP server set (read-only filtered at registration time)
- Output directory

**Selection**: URL parameter — `localhost:7860?persona=sre`

### Config Schema

```yaml
persona:
  default: "thinking-partner"
  profiles:
    thinking-partner:
      instruction: |
        You are a brainstorming partner. Help the user think through ideas.
        Ask probing questions. Challenge assumptions constructively.
        Suggest connections between ideas. Keep responses concise — 2-3 sentences max.
        When the user seems stuck, offer a different angle.
      tools:
        builtin: [websearch, file_read, file_write]
        mcp_servers: []
        mcp_read_only: true
      output:
        directory: "brainstorms"
    sre:
      instruction: |
        You are a Platform SRE voice assistant.
        Help the user investigate incidents, research cases, and collect diagnostic information.
        Use tools to search cases, look up KCS articles, and check Jira tickets.
        Keep spoken responses concise. Summarize findings clearly.
      tools:
        builtin: [websearch, file_read, file_write]
        mcp_servers: [redhat, jira]
        mcp_read_only: true
      output:
        directory: "/data/obsidian/SFDC"
```

## Stage 1.5 — Read-Only Information Gathering + File Output

### Tools (build order)

1. **Function calling framework** — prerequisite for everything
2. **WebSearch (Tavily)** — first tool, proves the framework
3. **File read/write** — scoped to output directory; can read past sessions
4. **MCP integration** — Red Hat + Jira, read-only tools only
5. **End-of-session LLM summary** — send transcript to Gemini, get structured summary
6. **NotebookLM sync** — if auth works (Python SDK), another write destination

### MCP Safety Model

- **Filter at registration time**: when Pipecat discovers MCP tools via `session.list_tools()`, only register tools matching read-only heuristics. Write tools never reach Gemini's function schema.
- Per-persona `mcp_servers` list controls which servers are connected.
- Global `mcp_read_only: true` flag enforces read-only filtering.

### End-of-Session Summary

- Auto-save raw transcript on disconnect (existing, keep it)
- LLM-generated summary via voice command ("summarize this session")
- Two separate concerns: never lose a transcript, summary is opt-in

### Code Organization

Single `bot.py` until ~300 lines. Extract when responsibilities clearly separate.

### Implementation Order

1. Rename to voxcat
2. Persona profile config schema (expand config.yaml)
3. Function calling framework + WebSearch (Tavily)
4. File read/write tools
5. MCP integration with read-only filtering
6. URL param persona selection
7. End-of-session LLM summary
8. NotebookLM sync (if auth is ready)

## Deferred (Stage 2+)

- Local CLI tool calling (complex permission control)
- Daily transport (SmallWebRTC is sufficient)
- Container deployment (local-first until stable)
- Model swap to Claude API / Hermes
- Pre-join lobby UI
- Multi-speaker diarization
- Slack MCP integration
- MCP write operations (create Jira, post Slack, add case comments)

## Decision Log

| # | Decision | Chosen | Alternatives Rejected |
|---|----------|--------|-----------------------|
| 1 | Product identity | Unified product, persona-driven roles | Separate products; SRE-only pivot |
| 2 | Next milestone | Function calling framework | Summary first; MCP first; containers |
| 3 | Transport | Stay SmallWebRTC | Daily; abstract both |
| 4 | Model | Gemini Live long-term | Claude API swap; evaluate both |
| 5 | Deployment | Local-first, containerize later | Container-first |
| 6 | Tool tiers | Core (always) + specialized (per-persona) | All available; strict allowlist |
| 7 | First tool | WebSearch (Tavily) | File write; summary |
| 8 | Config structure | Single config.yaml | Per-persona files |
| 9 | Persona selection | URL parameter | Config restart; voice command; lobby UI |
| 10 | WebSearch provider | Tavily | Google Custom Search; Brave |
| 11 | Function calling pattern | Pipecat FunctionSchema | Manual register_function |
| 12 | CLI tools | Deferred to Stage 2 | Allowlist; blocklist |
| 13 | MCP write blocking | Filter at registration time | Runtime interception |
| 14 | MCP servers for 1.5 | Red Hat + Jira | Red Hat only; all three including Slack |
| 15 | File operations | Read/write output dir, read past sessions | Write-only; read anywhere |
| 16 | MCP config style | Server names + read_only flag | Individual tool names |
| 17 | Summary timing | Stage 1.5, as function call | Defer to Stage 2 |
| 18 | NotebookLM | Stage 1.5 if auth works | Defer |
| 19 | Old design doc | Delete, replaced by this document | Keep as reference; update in-place |
