"""Tests for bot.py — build_system_instruction, build_pipeline, ContextGuardProcessor."""

from unittest.mock import MagicMock

from voxcat.bot import (
    COMMON_INSTRUCTION,
    TTS_STYLES,
    ContextGuardProcessor,
    build_system_instruction,
    _COMMON_VOICE,
    _COMMON_SILENT,
    _COMMON_BASE,
)


def test_build_system_instruction_voice_persona():
    persona = {"instruction": "You are a helper."}
    result = build_system_instruction(persona)
    assert "You are a helper." in result
    assert "Before calling ANY tool" in result
    assert "Never use markdown" in result


def test_build_system_instruction_silent_persona():
    persona = {"instruction": "Listen only.", "silent": True}
    result = build_system_instruction(persona)
    assert "Listen only." in result
    assert "continue listening" in result
    assert "Before calling ANY tool" not in result


def test_common_instruction_has_voice_prefix():
    assert COMMON_INSTRUCTION.startswith(_COMMON_VOICE)


def test_tts_styles_tuple():
    assert isinstance(TTS_STYLES, tuple)
    assert "extremely fast" in TTS_STYLES
    assert "sarcasm" in TTS_STYLES
    assert len(TTS_STYLES) == 5


def test_common_base_has_markdown_rule():
    assert "Never use markdown" in _COMMON_BASE


def test_common_base_has_url_rule():
    assert "Never read URLs aloud" in _COMMON_BASE


def test_common_base_has_barge_in_rule():
    assert "interrupts" in _COMMON_BASE
