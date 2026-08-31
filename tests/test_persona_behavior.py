"""Persona regression tests — calls Gemini API, run manually.

Usage:
    GOOGLE_API_KEY=... uv run pytest tests/test_persona_behavior.py -v -s

Skipped automatically if GOOGLE_API_KEY is not set.
Each test sends a few turns to Gemini Flash and asserts on behavior.
Cost: ~$0.01 per full run.
"""

import os
import re

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set — persona tests require live API",
)

MARKDOWN_RE = re.compile(r"\*\*|^#+\s|^-\s|`", re.MULTILINE)
URL_RE = re.compile(r"https?://\S+")
MODEL = "gemini-3.7-flash"


def load_persona_config(name: str) -> dict:
    from pathlib import Path
    import yaml

    config_path = Path(__file__).parent.parent / "src" / "voxcat" / "config.yaml.example"
    config = yaml.safe_load(config_path.read_text())
    return config["persona"]["profiles"][name]


async def chat(system_instruction: str, turns: list[str]) -> list[str]:
    """Send turns to Gemini and collect responses."""
    from google import genai

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    contents = []
    responses = []

    for user_msg in turns:
        contents.append({"role": "user", "parts": [{"text": user_msg}]})
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )
        text = response.text or ""
        responses.append(text)
        contents.append({"role": "model", "parts": [{"text": text}]})

    return responses


def word_count(text: str) -> int:
    return len(text.split())


# --- Thinking Partner ---

@pytest.mark.asyncio
async def test_thinking_partner_word_budget():
    persona = load_persona_config("thinking-partner")
    responses = await chat(persona["instruction"], [
        "I want to build a personal finance app",
        "It should track expenses and show charts",
    ])
    for r in responses:
        wc = word_count(r)
        assert wc <= 80, f"Thinking Partner exceeded word budget: {wc} words\n{r}"


@pytest.mark.asyncio
async def test_thinking_partner_no_markdown():
    persona = load_persona_config("thinking-partner")
    responses = await chat(persona["instruction"], [
        "What are the trade-offs between React and Vue for a dashboard?",
    ])
    for r in responses:
        assert not MARKDOWN_RE.search(r), f"Thinking Partner used markdown:\n{r}"


# --- Devil's Advocate ---

@pytest.mark.asyncio
async def test_devils_advocate_word_budget():
    persona = load_persona_config("devils-advocate")
    responses = await chat(persona["instruction"], [
        "We should rewrite our monolith in microservices",
        "But it will improve scalability",
    ])
    for r in responses:
        wc = word_count(r)
        assert wc <= 50, f"Devil's Advocate exceeded word budget: {wc} words\n{r}"


@pytest.mark.asyncio
async def test_devils_advocate_concedes():
    persona = load_persona_config("devils-advocate")
    responses = await chat(persona["instruction"], [
        "We should add input validation on our public API endpoints",
        "It prevents injection attacks and malformed data from reaching the database",
        "Every major framework recommends it and we've had two incidents without it",
    ])
    last = responses[-1].lower()
    concede_signals = ["hold", "concede", "valid", "agree", "right", "sound", "convinced", "fair"]
    assert any(s in last for s in concede_signals), (
        f"Devil's Advocate didn't concede after 3 rounds on a sound idea:\n{responses[-1]}"
    )


@pytest.mark.asyncio
async def test_devils_advocate_no_markdown():
    persona = load_persona_config("devils-advocate")
    responses = await chat(persona["instruction"], [
        "We should migrate our database to PostgreSQL",
    ])
    for r in responses:
        assert not MARKDOWN_RE.search(r), f"Devil's Advocate used markdown:\n{r}"


# --- SRE ---

@pytest.mark.asyncio
async def test_sre_word_budget():
    persona = load_persona_config("sre")
    responses = await chat(persona["instruction"], [
        "We're seeing high latency on the API gateway",
    ])
    for r in responses:
        wc = word_count(r)
        assert wc <= 50, f"SRE exceeded word budget: {wc} words\n{r}"


@pytest.mark.asyncio
async def test_sre_no_markdown():
    persona = load_persona_config("sre")
    responses = await chat(persona["instruction"], [
        "What should I check when a cluster node is not ready?",
    ])
    for r in responses:
        assert not MARKDOWN_RE.search(r), f"SRE used markdown:\n{r}"


@pytest.mark.asyncio
async def test_sre_no_urls():
    persona = load_persona_config("sre")
    responses = await chat(persona["instruction"], [
        "Where can I find documentation on OpenShift networking?",
    ])
    for r in responses:
        assert not URL_RE.search(r), f"SRE read a URL aloud:\n{r}"


# --- Note Taker ---

@pytest.mark.asyncio
async def test_note_taker_stays_silent():
    persona = load_persona_config("note-taker")
    responses = await chat(persona["instruction"], [
        "So the main issue is that our deployment pipeline takes 45 minutes",
        "We think the bottleneck is the integration test suite",
    ])
    for r in responses:
        wc = word_count(r)
        assert wc <= 10, f"Note Taker spoke when it should be silent: {wc} words\n{r}"
