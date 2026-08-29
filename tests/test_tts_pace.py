from pipecat.frames.frames import TextFrame
from pipecat.processors.frame_processor import FrameDirection

from voxcat.bot import TTSPaceProcessor


async def test_prepends_tag_to_first_frame():
    proc = TTSPaceProcessor("fast")
    frame = TextFrame(text="Hello world")
    await proc.process_frame(frame, FrameDirection.DOWNSTREAM)
    assert frame.text == "[fast] Hello world"


async def test_no_tag_on_subsequent_frames():
    proc = TTSPaceProcessor("fast")
    f1 = TextFrame(text="First")
    f2 = TextFrame(text="Second")
    await proc.process_frame(f1, FrameDirection.DOWNSTREAM)
    await proc.process_frame(f2, FrameDirection.DOWNSTREAM)
    assert f2.text == "Second"


async def test_resets_on_empty_text():
    proc = TTSPaceProcessor("slow")
    f1 = TextFrame(text="Sentence one.")
    f2 = TextFrame(text="")
    f3 = TextFrame(text="Sentence two.")
    await proc.process_frame(f1, FrameDirection.DOWNSTREAM)
    await proc.process_frame(f2, FrameDirection.DOWNSTREAM)
    await proc.process_frame(f3, FrameDirection.DOWNSTREAM)
    assert f1.text == "[slow] Sentence one."
    assert f3.text == "[slow] Sentence two."


async def test_custom_pace_tag():
    proc = TTSPaceProcessor("medium")
    frame = TextFrame(text="Test")
    await proc.process_frame(frame, FrameDirection.DOWNSTREAM)
    assert frame.text == "[medium] Test"
