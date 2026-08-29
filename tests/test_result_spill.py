import json

import pytest

from pipecat.frames.frames import FunctionCallResultFrame, TextFrame
from pipecat.processors.frame_processor import FrameDirection

from bot import ResultSpillProcessor


class FakeFrameCollector:
    """Collects frames pushed by the processor."""
    def __init__(self):
        self.frames = []

    async def __call__(self, frame, direction):
        self.frames.append(frame)


@pytest.fixture
def spill(tmp_path):
    return ResultSpillProcessor(str(tmp_path), threshold=100, preview_size=50)


@pytest.mark.asyncio
async def test_small_result_passes_through(spill):
    frame = FunctionCallResultFrame(
        function_name="web_search",
        tool_call_id="tc1",
        arguments={"query": "test"},
        result={"status": "ok"},
    )
    original_result = frame.result.copy()
    await spill.process_frame(frame, FrameDirection.DOWNSTREAM)
    assert frame.result == original_result


@pytest.mark.asyncio
async def test_large_result_spills_to_file(spill, tmp_path):
    big_data = {"items": [{"name": f"item-{i}", "value": "x" * 50} for i in range(10)]}
    frame = FunctionCallResultFrame(
        function_name="search_cases",
        tool_call_id="tc2",
        arguments={},
        result=big_data,
    )
    await spill.process_frame(frame, FrameDirection.DOWNSTREAM)

    assert frame.result["truncated"] is True
    assert "full_result_file" in frame.result
    assert frame.result["note"] == "Result too large. Preview shown. Use file_read to see the full data."
    assert len(frame.result["preview"]) == 50

    spill_path = tmp_path / "tool-results"
    spill_files = list(spill_path.glob("search_cases-*.json"))
    assert len(spill_files) == 1
    saved = json.loads(spill_files[0].read_text())
    assert saved == big_data


@pytest.mark.asyncio
async def test_non_function_frame_passes_through(spill):
    frame = TextFrame(text="hello")
    await spill.process_frame(frame, FrameDirection.DOWNSTREAM)
    assert frame.text == "hello"


@pytest.mark.asyncio
async def test_result_at_threshold_not_spilled(spill):
    result = {"x": "a" * 80}
    serialized = json.dumps(result, default=str, ensure_ascii=False)
    assert len(serialized) <= 100

    frame = FunctionCallResultFrame(
        function_name="test_tool",
        tool_call_id="tc3",
        arguments={},
        result=result,
    )
    await spill.process_frame(frame, FrameDirection.DOWNSTREAM)
    assert "truncated" not in frame.result
