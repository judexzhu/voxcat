# Package Voxcat as uv tool

## Goal

`uv tool install git+https://github.com/user/voxcat` then `voxcat` to run.

## Plan

### 1. Restructure into proper package

Move modules into `src/voxcat/`:
```
src/voxcat/
  __init__.py
  cli.py          ← entry point (argparse: --port, --config)
  bot.py           ← run_bot() pipeline logic
  tools.py
  transcript.py
  mcp_connect.py
  filestore.py
```

### 2. Entry point

```toml
[project.scripts]
voxcat = "voxcat.cli:main"
```

`cli.py` handles:
- `voxcat` — start server (default config)
- `voxcat --config path/to/config.yaml` — custom config
- `voxcat --port 8080` — custom port
- `voxcat init` — copy default config + mcp_servers.json to `~/.config/voxcat/`

### 3. Package data

Include in the package:
- `client/dist/` as static assets
- Default `config.yaml` (no MCP servers, just built-in tools)
- Default `mcp_servers.json` (empty template)

Use `importlib.resources` for resolving paths inside installed package.

### 4. MCP config separation

Split current config:
- `mcp_servers.json` — standard MCP format, server definitions
- `config.yaml` — voxcat config, personas reference servers by name + allow_tools

```yaml
# config.yaml persona section
sre:
  tools:
    mcp_servers:
      - name: redhat
        allow_tools: [search_cases, get_case]
```

Update `mcp_connect.py` to read from JSON, merge allow_tools from YAML.

### 5. File paths

All file paths (output/, sessions/, config) resolve relative to CWD or `~/.config/voxcat/`. Not relative to package install location.

### 6. .env handling

`python-dotenv` loads from CWD. Document that users create `.env` in their working directory.

## Effort

~2 hours. File moves, path resolution, entry point, packaging config.

## Priority

Next session — after current features stabilize.
