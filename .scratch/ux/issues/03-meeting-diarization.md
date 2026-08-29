# Post-session speaker diarization for meeting notes

## Goal

Note Taker persona records a meeting, then post-processes the audio with speaker diarization to produce a labeled transcript (Speaker 1, Speaker 2, etc.).

## Plan

### 1. Record session audio (~30 lines)

Add a `AudioRecorderProcessor` that saves PCM frames to a WAV file in `sessions/{persona}/`.

```python
# In bot.py pipeline (silent mode):
recorder_proc = AudioRecorderProcessor(output_path)
pipeline = Pipeline([
    transport.input(),
    recorder_proc,  # taps audio frames, writes to WAV
    stt,
    user_aggregator,
    llm,
    transport.output(),
    assistant_aggregator,
])
```

Pipecat frames carry raw PCM at 16kHz/24kHz. Write a WAV header on start, append frames, finalize on disconnect.

### 2. Post-session diarization (~30 lines)

On disconnect, call `gemini-3.5-transcribe` (batch, not live) with diarization:

```python
from google import genai

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
response = client.models.generate_content(
    model="gemini-3.5-transcribe",
    contents=genai.types.Content(parts=[
        genai.types.Part(inline_data=genai.types.Blob(
            mime_type="audio/wav",
            data=audio_bytes,
        ))
    ]),
    config=genai.types.GenerateContentConfig(
        transcription_config=genai.types.TranscriptionConfig(
            diarization_mode="speaker",
        ),
    ),
)
```

### 3. Save enhanced transcript (~20 lines)

Parse diarized response, format as:

```markdown
# Meeting Notes: {topic}
**Date:** 2026-08-28 | **Speakers:** 3

**[14:02:11] Speaker 1:** Let's discuss the output directories...
**[14:02:19] Speaker 2:** What about scoped roots?
**[14:02:34] Speaker 1:** Good point, let's go with that.
```

Save alongside or replace the original session file.

### 4. UI: ENHANCE button (~10 lines)

In past sessions view, add "ENHANCE" button next to CONTINUE SESSION. Calls `POST /api/sessions/{persona}/{filename}/enhance`. Shows progress, replaces transcript when done.

## Limitations

- Only works with in-person meetings where all speakers are on the same mic
- Remote meetings (Zoom/Teams) need system audio capture (macOS virtual audio device — separate problem)
- Batch API has 30-minute limit with diarization enabled
- Diarization labels are generic (Speaker 1, 2) — no name mapping

## Priority

Medium — builds on existing Note Taker silent mode. Next session.
