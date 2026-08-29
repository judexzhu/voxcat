import os
from unittest.mock import MagicMock

from voxcat.tools import build_tools


def test_registers_requested_tools(tmp_path):
    recorder = MagicMock()
    os.environ["TAVILY_API_KEY"] = "test-key"
    try:
        tools = build_tools(["file_read", "file_write", "websearch"], str(tmp_path), recorder)
        names = {t.name for t in tools}
        assert names == {"file_read", "file_write", "web_search"}
    finally:
        del os.environ["TAVILY_API_KEY"]


def test_skips_unavailable_tools(tmp_path):
    recorder = MagicMock()
    old = os.environ.pop("TAVILY_API_KEY", None)
    try:
        tools = build_tools(["file_read", "websearch"], str(tmp_path), recorder)
        names = {t.name for t in tools}
        assert "file_read" in names
        assert "web_search" not in names
    finally:
        if old:
            os.environ["TAVILY_API_KEY"] = old


def test_empty_list_returns_empty(tmp_path):
    recorder = MagicMock()
    tools = build_tools([], str(tmp_path), recorder)
    assert tools == []


def test_all_builtin_tools_register(tmp_path):
    recorder = MagicMock()
    os.environ["TAVILY_API_KEY"] = "test-key"
    os.environ["NOTEBOOKLM_NOTEBOOK_ID"] = "test-id"
    try:
        all_names = [
            "websearch", "web_read", "file_read", "file_write", "file_list",
            "summarize_session", "get_current_time", "deep_analysis", "research",
            "notebooklm_sync",
        ]
        tools = build_tools(all_names, str(tmp_path), recorder)
        assert len(tools) == 10
    finally:
        del os.environ["TAVILY_API_KEY"]
        del os.environ["NOTEBOOKLM_NOTEBOOK_ID"]
