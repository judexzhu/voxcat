"""Tests for REST API routes via FastAPI TestClient."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from voxcat.api import register_routes


def _make_app(tmp_path):
    output_dir = tmp_path / "output" / "test-persona"
    output_dir.mkdir(parents=True)
    sessions_dir = tmp_path / "sessions"

    config = {
        "persona": {
            "default": "test-persona",
            "profiles": {
                "test-persona": {
                    "label": "Test Persona",
                    "description": "A test persona.",
                    "output": {"directory": str(output_dir)},
                },
            },
        },
    }
    app = FastAPI()
    register_routes(app, config, ["test-persona"], sessions_dir)
    return TestClient(app), output_dir, sessions_dir


def test_list_personas(tmp_path):
    client, _, _ = _make_app(tmp_path)
    r = client.get("/api/personas")
    assert r.status_code == 200
    data = r.json()
    assert data["default"] == "test-persona"
    assert len(data["personas"]) == 1
    assert data["personas"][0]["label"] == "Test Persona"


def test_file_tree(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / "notes.md").write_text("hello")
    r = client.get("/api/files/tree")
    assert r.status_code == 200
    tree = r.json()["tree"]
    assert len(tree) == 1
    assert tree[0]["persona"] == "test-persona"
    assert any(f["name"] == "notes.md" for f in tree[0]["files"])


def test_list_files(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / "a.md").write_text("aaa")
    r = client.get("/api/files", params={"persona": "test-persona"})
    assert r.status_code == 200
    assert len(r.json()["files"]) == 1


def test_read_file(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / "doc.md").write_text("content here")
    r = client.get("/api/files/doc.md", params={"persona": "test-persona"})
    assert r.status_code == 200
    assert r.json()["content"] == "content here"


def test_read_file_not_found(tmp_path):
    client, _, _ = _make_app(tmp_path)
    r = client.get("/api/files/nope.md", params={"persona": "test-persona"})
    assert "error" in r.json()


def test_read_file_unknown_persona(tmp_path):
    client, _, _ = _make_app(tmp_path)
    r = client.get("/api/files/x.md", params={"persona": "unknown"})
    assert r.status_code == 404


def test_delete_file(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / "delete-me.md").write_text("bye")
    r = client.delete("/api/files/delete-me.md", params={"persona": "test-persona"})
    assert r.json()["deleted"] == "delete-me.md"
    assert not (output_dir / "delete-me.md").exists()


def test_rename_file(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / "old.md").write_text("data")
    r = client.post("/api/files/old.md/rename", params={"persona": "test-persona", "new_name": "new.md"})
    assert r.json()["filename"] == "new.md"
    assert (output_dir / "new.md").exists()
    assert not (output_dir / "old.md").exists()


def test_rename_file_adds_extension(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / "x.md").write_text("data")
    r = client.post("/api/files/x.md/rename", params={"persona": "test-persona", "new_name": "renamed"})
    assert r.json()["filename"] == "renamed.md"


def test_list_sessions_empty(tmp_path):
    client, _, _ = _make_app(tmp_path)
    r = client.get("/api/sessions")
    assert r.json()["sessions"] == []


def test_list_sessions(tmp_path):
    client, _, sessions_dir = _make_app(tmp_path)
    (sessions_dir / "test-persona").mkdir(parents=True)
    (sessions_dir / "test-persona" / "2026-08-29.md").write_text("session")
    r = client.get("/api/sessions")
    sessions = r.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["persona"] == "test-persona"


def test_read_session(tmp_path):
    client, _, sessions_dir = _make_app(tmp_path)
    (sessions_dir / "test-persona").mkdir(parents=True)
    (sessions_dir / "test-persona" / "s.md").write_text("transcript here")
    r = client.get("/api/sessions/test-persona/s.md")
    assert r.json()["content"] == "transcript here"


def test_read_session_not_found(tmp_path):
    client, _, sessions_dir = _make_app(tmp_path)
    (sessions_dir / "test-persona").mkdir(parents=True)
    r = client.get("/api/sessions/test-persona/nope.md")
    assert "error" in r.json()


def test_delete_session(tmp_path):
    client, _, sessions_dir = _make_app(tmp_path)
    (sessions_dir / "p").mkdir(parents=True)
    (sessions_dir / "p" / "s.md").write_text("bye")
    r = client.delete("/api/sessions/p/s.md")
    assert r.json()["deleted"] == "s.md"


def test_rename_session(tmp_path):
    client, _, sessions_dir = _make_app(tmp_path)
    (sessions_dir / "p").mkdir(parents=True)
    (sessions_dir / "p" / "old.md").write_text("data")
    r = client.post("/api/sessions/p/old.md/rename", params={"new_name": "new"})
    assert r.json()["filename"] == "new.md"


def test_nlm_sources_without_env(tmp_path):
    client, _, _ = _make_app(tmp_path)
    r = client.get("/api/notebooklm/sources")
    assert r.json()["sources"] == []


def test_nlm_source_content_without_env(tmp_path):
    client, _, _ = _make_app(tmp_path)
    r = client.get("/api/notebooklm/sources/some-id")
    assert "error" in r.json()


def test_file_tree_excludes_dotfiles(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    (output_dir / ".DS_Store").write_text("")
    (output_dir / "visible.md").write_text("hi")
    r = client.get("/api/files/tree")
    files = r.json()["tree"][0]["files"]
    names = [f["name"] for f in files]
    assert "visible.md" in names
    assert ".DS_Store" not in names


def test_path_traversal_blocked(tmp_path):
    client, output_dir, _ = _make_app(tmp_path)
    secret = tmp_path / "secret.txt"
    secret.write_text("private")
    r = client.get("/api/files/../../secret.txt", params={"persona": "test-persona"})
    assert "error" in r.json() or r.status_code == 404
