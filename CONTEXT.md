# Voxcat — Domain Glossary

## Terms

- **Session**: A single voice conversation from connect to disconnect. Produces one transcript file in the persona's output directory.
- **Persona**: A profile that shapes the agent's behavior. Includes: system instruction, built-in tool set, MCP server set (read-only filtered), and output directory. Selected via URL parameter.
- **Transcript**: The raw record of a session — timestamped turns with role labels. Written live during the session, saved on disconnect.
- **Summary**: A structured document generated from the transcript containing key ideas, decisions, action items, and open questions. Triggered by voice command or explicit request.
- **Transport**: The I/O layer connecting the user to the pipeline. SmallWebRTC for browser access.
- **Pipeline**: The Pipecat frame processor chain: transport input → context aggregation → Gemini Live → transport output → context aggregation.
- **Tool**: A function the agent can invoke mid-conversation via Gemini Live function calling. Built-in tools (WebSearch, file ops) are always available per persona config. MCP tools are discovered dynamically from connected servers, filtered to read-only at registration time.
- **MCP Server**: An external tool provider connected via Model Context Protocol. Persona config controls which servers are connected. Write operations are blocked by filtering tools at registration time — Gemini never sees write tool schemas.
