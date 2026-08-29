# Large tool result handling — spill-to-file pattern

## Status: IMPLEMENTED (2026-08-29)

## Problem

MCP tools (Jira, Red Hat API) can return 50-100K+ chars of JSON. Pipecat feeds the full result into LLM context, causing: context overflow, degraded reasoning quality, repeated tool calls, and mid-sentence cutoffs.

## Solution: ResultSpillProcessor

`FrameProcessor` in `bot.py` that intercepts `FunctionCallResultFrame` downstream before the context aggregator stores it.

**Flow:**
1. Serialize `frame.result` to JSON
2. If `len(serialized) > threshold` (default 5000 chars):
   - Write full result to `output/<persona>/tool-results/<tool>-<timestamp>.json`
   - Replace `frame.result` with: 2000-char preview + file path + instruction to use `file_read`
3. If under threshold: pass through unchanged
4. Push frame downstream to aggregator (stores truncated version in LLM context)

**LLM sees:**
```json
{
  "preview": "<first 2000 chars of original JSON>",
  "truncated": true,
  "full_size_chars": 87432,
  "full_result_file": "tool-results/search_cases-20260829-143022.json",
  "note": "Result too large. Preview shown. Use file_read to see the full data."
}
```

**Agent can** call `file_read` on the spilled file if it needs more data. Most questions are answerable from the preview alone.

## Pipeline placement

All three pipelines: `... llm, result_spill, [pace_proc], [tts], transport.output(), assistant_aggregator`

Placed after LLM (which emits the result frame downstream) and before assistant_aggregator (which stores it in context).

## Tests

4 tests in `tests/test_result_spill.py`:
- Small result passes through unchanged
- Large result spills to file + creates truncated frame
- Non-function frames pass through
- Result at exact threshold not spilled

## Open: threshold tuning

Current threshold (5000 chars / ~1250 tokens) is a workaround. Needs real usage data to find the optimal value. Factors:

- **Per-result quality**: LLM reasons worse over large JSON blobs
- **Accumulation**: results stack across session turns. 30 calls x 5K = 150K chars in context
- **Model-dependent**: different Gemini models may handle large contexts differently
- **Task-dependent**: SRE searches benefit from more preview, brainstorming needs less

Investigation needed: log actual tool result sizes in production, measure answer quality at different thresholds, check if Gemini 3.7 Flash degrades at specific context sizes. Consider making threshold configurable per-tool in `config.yaml`.

## Spilled file cleanup

Currently: spilled files persist in `output/<persona>/tool-results/`. They are useful artifacts (full search results, case data). No auto-cleanup implemented. Could add session-end cleanup or TTL-based cleanup later if disk usage becomes an issue.
