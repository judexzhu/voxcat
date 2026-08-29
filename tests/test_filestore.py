from pathlib import Path

from filestore import safe_resolve


def test_valid_filename_resolves(tmp_path):
    (tmp_path / "notes.md").touch()
    result = safe_resolve(tmp_path, "notes.md")
    assert result == tmp_path / "notes.md"


def test_traversal_returns_none(tmp_path):
    result = safe_resolve(tmp_path, "../../etc/passwd")
    assert result is None


def test_subdirectory_resolves(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "file.txt").touch()
    result = safe_resolve(tmp_path, "sub/file.txt")
    assert result == sub / "file.txt"


def test_nonexistent_file_still_resolves(tmp_path):
    result = safe_resolve(tmp_path, "doesnt-exist.md")
    assert result is not None
    assert result == tmp_path / "doesnt-exist.md"
