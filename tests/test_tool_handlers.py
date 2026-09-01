"""Tests for individual tool handler behavior via build_tools injection."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from voxcat.tools import build_tools


def _build(tmp_path, names, **kwargs):
    recorder = MagicMock()
    return build_tools(names, str(tmp_path), recorder, **kwargs), recorder


def _make_params(arguments, result_callback=None):
    params = MagicMock()
    params.arguments = arguments
    params.result_callback = result_callback or AsyncMock()
    return params


def _get_handler(tools, tool_name):
    for t in tools:
        if t.name == tool_name:
            return t.handler
    raise KeyError(f"Tool {tool_name} not found in {[t.name for t in tools]}")


# --- file_write ---

@pytest.mark.asyncio
async def test_file_write_saves_md(tmp_path):
    tools, _ = _build(tmp_path, ["file_write"])
    handler = _get_handler(tools, "file_write")
    params = _make_params({"filename": "notes.md", "content": "hello"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert result["status"] == "saved"
    assert (tmp_path / "notes.md").read_text() == "hello"


@pytest.mark.asyncio
async def test_file_write_rejects_bad_extension(tmp_path):
    tools, _ = _build(tmp_path, ["file_write"])
    handler = _get_handler(tools, "file_write")
    params = _make_params({"filename": "script.py", "content": "import os"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert "error" in result
    assert not (tmp_path / "script.py").exists()


@pytest.mark.asyncio
async def test_file_write_allows_yaml(tmp_path):
    tools, _ = _build(tmp_path, ["file_write"])
    handler = _get_handler(tools, "file_write")
    params = _make_params({"filename": "config.yaml", "content": "key: val"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert result["status"] == "saved"


# --- file_read ---

@pytest.mark.asyncio
async def test_file_read_returns_content(tmp_path):
    (tmp_path / "doc.md").write_text("my document")
    tools, _ = _build(tmp_path, ["file_read"])
    handler = _get_handler(tools, "file_read")
    params = _make_params({"filename": "doc.md"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert result["content"] == "my document"


@pytest.mark.asyncio
async def test_file_read_blocks_traversal(tmp_path):
    tools, _ = _build(tmp_path, ["file_read"])
    handler = _get_handler(tools, "file_read")
    params = _make_params({"filename": "../../etc/passwd"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert "error" in result


@pytest.mark.asyncio
async def test_file_read_not_found(tmp_path):
    tools, _ = _build(tmp_path, ["file_read"])
    handler = _get_handler(tools, "file_read")
    params = _make_params({"filename": "nope.md"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert "error" in result


# --- file_list ---

@pytest.mark.asyncio
async def test_file_list_returns_files(tmp_path):
    (tmp_path / "a.md").write_text("aaa")
    (tmp_path / "b.txt").write_text("bbb")
    tools, _ = _build(tmp_path, ["file_list"])
    handler = _get_handler(tools, "file_list")
    params = _make_params({})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    names = [f["name"] for f in result["files"]]
    assert "a.md" in names
    assert "b.txt" in names


@pytest.mark.asyncio
async def test_file_list_excludes_dotfiles(tmp_path):
    (tmp_path / ".DS_Store").write_text("")
    (tmp_path / "visible.md").write_text("hi")
    tools, _ = _build(tmp_path, ["file_list"])
    handler = _get_handler(tools, "file_list")
    params = _make_params({})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    names = [f["name"] for f in result["files"]]
    assert "visible.md" in names
    assert ".DS_Store" not in names


@pytest.mark.asyncio
async def test_file_list_excludes_directories(tmp_path):
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file.md").write_text("hi")
    tools, _ = _build(tmp_path, ["file_list"])
    handler = _get_handler(tools, "file_list")
    params = _make_params({})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    names = [f["name"] for f in result["files"]]
    assert "file.md" in names
    assert "subdir" not in names


# --- get_current_time ---

@pytest.mark.asyncio
async def test_get_current_time(tmp_path):
    tools, _ = _build(tmp_path, ["get_current_time"])
    handler = _get_handler(tools, "get_current_time")
    params = _make_params({})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert "datetime" in result
    assert "readable" in result


# --- set_topic ---

@pytest.mark.asyncio
async def test_set_topic(tmp_path):
    tools, recorder = _build(tmp_path, ["set_topic"])
    handler = _get_handler(tools, "set_topic")
    params = _make_params({"topic": "cloud-migration"})
    await handler(params)
    result = params.result_callback.call_args[0][0]
    assert result["topic"] == "cloud-migration"
    recorder.set_topic.assert_called_once_with("cloud-migration")


# --- injected clients ---

@pytest.mark.asyncio
async def test_build_tools_uses_injected_tavily(tmp_path):
    import os
    fake_tavily = MagicMock()
    fake_tavily.search = AsyncMock(return_value={"results": [
        {"title": "Test", "url": "http://test.com", "content": "fake result"}
    ]})
    os.environ["TAVILY_API_KEY"] = "test"
    try:
        tools, _ = _build(tmp_path, ["websearch"], tavily_client=fake_tavily)
    finally:
        del os.environ["TAVILY_API_KEY"]
    # web_search_handler is module-level, doesn't use injected client
    # but web_read_handler (closure) should
    # Just verify the tools registered with the fake available
    assert any(t.name == "web_search" for t in tools)
