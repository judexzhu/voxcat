from unittest.mock import AsyncMock, MagicMock

from voxcat.bot import apply_tts_style


async def test_applies_style_tag_to_every_call():
    results = []

    async def mock_run_tts(text, context_id):
        results.append(text)
        return
        yield  # make it an async generator

    tts = MagicMock()
    tts.run_tts = mock_run_tts

    apply_tts_style(tts, "extremely fast")

    async for _ in tts.run_tts("Hello world.", "ctx1"):
        pass
    async for _ in tts.run_tts("Second sentence.", "ctx2"):
        pass

    assert results[0] == "[extremely fast] Hello world."
    assert results[1] == "[extremely fast] Second sentence."


async def test_skips_empty_text():
    results = []

    async def mock_run_tts(text, context_id):
        results.append(text)
        return
        yield

    tts = MagicMock()
    tts.run_tts = mock_run_tts

    apply_tts_style(tts, "whispering")

    async for _ in tts.run_tts("  ", "ctx1"):
        pass

    assert results[0] == "  "
