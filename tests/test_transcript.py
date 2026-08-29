from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from transcript import TranscriptRecorder


def test_add_turn_and_get_text():
    r = TranscriptRecorder("output/test", persona="test")
    ts = datetime(2026, 8, 29, 14, 30, 0)
    r.add_turn("user", "Hello", ts)
    r.add_turn("assistant", "Hi there", ts)
    text = r.get_transcript_text()
    assert "[14:30:00] User: Hello" in text
    assert "[14:30:00] Assistant: Hi there" in text


def test_save_transcript_creates_file(tmp_path):
    r = TranscriptRecorder(str(tmp_path), persona="test")
    r.add_turn("user", "test message")
    path = r.save_transcript()
    assert path.exists()
    content = path.read_text()
    assert "test message" in content
    assert "## Key Ideas" in content
    assert "## Raw Transcript" in content


def test_save_session_creates_file(tmp_path):
    with patch("transcript.SESSIONS_DIR", tmp_path):
        r = TranscriptRecorder("output/test", persona="mybot")
        r.add_turn("user", "session content")
        path = r.save_session()
        assert path.exists()
        assert path.parent.name == "mybot"
        content = path.read_text()
        assert "session content" in content
        assert "# Session: mybot" in content


def test_save_session_appends_with_separator(tmp_path):
    with patch("transcript.SESSIONS_DIR", tmp_path):
        r1 = TranscriptRecorder("output/test", persona="bot")
        r1.add_turn("user", "first session")
        path = r1.save_session()

        r2 = TranscriptRecorder("output/test", persona="bot")
        r2.add_turn("user", "continued session")
        path2 = r2.save_session(append_to=path.name)
        assert path2 == path
        content = path.read_text()
        assert "first session" in content
        assert "---" in content
        assert "Continued:" in content
        assert "continued session" in content
