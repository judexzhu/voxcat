# Large MCP tool results cause bot to stop mid-sentence

## Problem

When MCP tools (especially `jira_search_issues`) return large JSON payloads, Gemini Live hits its output token limit and stops speaking mid-sentence. The user sees a partial response like "The search concluded because the tool returned" and then silence.

## Root cause

Pipecat feeds the full MCP tool result back into the LLM context. A Jira search returning 20+ issues is thousands of tokens. Gemini Live's output budget is consumed by processing the large context, leaving nothing for the spoken response.

## Plan

### Option A: Truncate at the pipeline level (recommended)

Add a result-truncation wrapper around MCP tool results in `bot.py` before they enter the LLM context.

1. After `connect_mcp_servers()` returns tools, wrap each tool's handler to truncate results
2. Truncation rules:
   - Arrays (issues, results): keep first 5 items, append `"... and N more"`
   - String content: cap at 3000 chars
   - Nested objects: flatten to key fields only
3. The FULL result still goes to the RTVI data channel (client sees everything), only the LLM gets the truncated version

Implementation sketch in `bot.py`:
```python
def truncate_for_llm(result, max_items=5, max_chars=3000):
    if isinstance(result, dict):
        for key in ("issues", "results", "items"):
            if key in result and isinstance(result[key], list):
                items = result[key]
                if len(items) > max_items:
                    result[key] = items[:max_items]
                    result[f"_{key}_truncated"] = f"{len(items) - max_items} more not shown"
    if isinstance(result, str) and len(result) > max_chars:
        result = result[:max_chars] + "... (truncated)"
    return result
```

### Option B: Per-tool max_results parameter

Configure `max_results` per MCP tool in `config.yaml` and pass it as a default argument. Only works for tools that support pagination/limits.

### Option C: Summarize via Gemini Flash

For results > N tokens, call Gemini 3.7 Flash to summarize before feeding back. Adds latency but preserves all information.

## Recommendation

Start with Option A — simple, no latency, covers 90% of cases. Add Option C later for research-heavy tools where truncation loses too much.

## Priority

Medium — affects SRE persona most (Jira/case searches). Other personas rarely hit this.
