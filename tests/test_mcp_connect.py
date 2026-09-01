"""Tests for mcp_connect.py — config parsing and env validation."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voxcat.mcp_connect import connect_mcp_servers


@pytest.mark.asyncio
async def test_skips_unconfigured_server():
    tools, clients = await connect_mcp_servers(["nonexistent"], {})
    assert tools == []
    assert clients == []


@pytest.mark.asyncio
async def test_skips_server_with_missing_env():
    config = {
        "myserver": {
            "command": "python",
            "args": ["-m", "server"],
            "env_keys": ["MISSING_KEY_XYZ"],
        }
    }
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MISSING_KEY_XYZ", None)
        tools, clients = await connect_mcp_servers(["myserver"], config)
    assert tools == []
    assert clients == []


@pytest.mark.asyncio
async def test_handles_connection_failure():
    config = {
        "badserver": {
            "command": "nonexistent-binary-xyz",
            "args": [],
            "env_keys": [],
        }
    }
    tools, clients = await connect_mcp_servers(["badserver"], config)
    assert tools == []
    assert clients == []
