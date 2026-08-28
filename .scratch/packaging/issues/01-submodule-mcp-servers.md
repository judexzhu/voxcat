Status: needs-triage

# Add MCP servers as git submodules

When pushing to GitHub or building Docker image, add `mcp-redhat` and `mcp-jira` as git submodules under `mcp-servers/`. Update `config.yaml` paths from absolute (`/Users/judzhu/...`) to relative (`./mcp-servers/redhat`).

**Trigger:** First GitHub push or Dockerfile creation.

**Steps:**
1. `git submodule add <mcp-redhat-url> mcp-servers/redhat`
2. `git submodule add <mcp-jira-url> mcp-servers/jira`
3. Update `config.yaml` cwd paths to `./mcp-servers/redhat` and `./mcp-servers/jira`
4. Verify `uv run` works from the submodule paths
