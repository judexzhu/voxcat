import os

from loguru import logger
from pipecat.services.mcp_service import MCPClient


async def connect_mcp_servers(
    server_names: list[str], mcp_config: dict,
) -> tuple[list, list[MCPClient]]:
    from mcp import StdioServerParameters

    all_tools = []
    clients = []
    for name in server_names:
        server = mcp_config.get(name)
        if not server:
            logger.warning(f"MCP server not configured: {name}")
            continue
        env_keys = server.get("env_keys", [])
        missing = [k for k in env_keys if not os.environ.get(k)]
        if missing:
            logger.warning(f"MCP server {name} skipped: missing env vars {missing}")
            continue
        env = {k: os.environ[k] for k in env_keys if os.environ.get(k)}
        env["PATH"] = os.environ.get("PATH", "")
        cwd = server.get("cwd")
        client = MCPClient(
            server_params=StdioServerParameters(
                command=server["command"],
                args=server.get("args", []),
                env=env,
                cwd=cwd,
            ),
            tools_filter=server.get("read_only_tools"),
        )
        try:
            mcp_tools = await client.tools()
            tool_list = mcp_tools.standard_tools
            all_tools.extend(tool_list)
            clients.append(client)
            logger.info(f"MCP server {name}: {len(tool_list)} tools registered")
        except Exception as e:
            logger.error(f"MCP server {name} failed to connect: {e}")
    return all_tools, clients
