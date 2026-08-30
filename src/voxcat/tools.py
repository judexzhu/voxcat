import os
from datetime import datetime
from pathlib import Path

from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.services.llm_service import FunctionCallParams

from .filestore import safe_resolve
from .transcript import TranscriptRecorder


async def web_search_handler(params: FunctionCallParams):
    from tavily import AsyncTavilyClient

    query = params.arguments["query"]
    logger.info(f"WebSearch: {query}")
    client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    response = await client.search(query=query, max_results=5)
    results = [
        {"title": r["title"], "url": r["url"], "content": r["content"][:500]}
        for r in response.get("results", [])
    ]
    await params.result_callback({"results": results})


async def get_current_time_handler(params: FunctionCallParams):
    now = datetime.now()
    await params.result_callback({
        "datetime": now.isoformat(),
        "readable": now.strftime("%A, %B %d, %Y at %I:%M %p"),
    })


async def deep_analysis_handler(params: FunctionCallParams):
    from google import genai

    query = params.arguments["query"]
    context = params.arguments.get("context", "")
    logger.info(f"DeepAnalysis: {query[:100]}")
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    prompt = f"{query}\n\nContext:\n{context}" if context else query
    response = await client.aio.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            thinking_config=genai.types.ThinkingConfig(thinking_budget=8192),
        ),
    )
    await params.result_callback({"analysis": response.text[:5000]})


async def research_handler(params: FunctionCallParams):
    from google import genai
    from tavily import AsyncTavilyClient

    topic = params.arguments["topic"]
    logger.info(f"Research: {topic}")
    tavily = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    search_response = await tavily.search(query=topic, max_results=5)
    results = search_response.get("results", [])
    logger.info(f"Research: found {len(results)} search results")

    urls = [r["url"] for r in results[:3]]
    extracted = []
    if urls:
        extract_response = await tavily.extract(urls=urls)
        for r in extract_response.get("results", []):
            extracted.append({"url": r["url"], "content": r["raw_content"][:3000]})
    logger.info(f"Research: extracted {len(extracted)} pages")

    sources_text = "\n\n".join(
        f"Source: {e['url']}\n{e['content']}" for e in extracted
    )
    snippets_text = "\n".join(
        f"- {r['title']}: {r['content'][:200]}" for r in results
    )

    prompt = (
        f"Research topic: {topic}\n\n"
        f"Search snippets:\n{snippets_text}\n\n"
        f"Full page content:\n{sources_text}\n\n"
        "Synthesize a structured research report with: Key Findings, Details, Sources, and Open Questions."
    )

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = await client.aio.models.generate_content(
        model="gemini-3.7-flash",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            thinking_config=genai.types.ThinkingConfig(thinking_budget=8192),
        ),
    )
    await params.result_callback({"report": response.text[:5000]})


async def notebooklm_sync_handler(params: FunctionCallParams):
    from notebooklm import NotebookLMClient

    title = params.arguments["title"]
    content = params.arguments["content"]
    notebook_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "")
    if not notebook_id:
        await params.result_callback({"error": "NOTEBOOKLM_NOTEBOOK_ID not set"})
        return
    logger.info(f"NotebookLM sync: {title}")
    async with NotebookLMClient.from_storage() as client:
        await client.sources.add_text(
            notebook_id=notebook_id, title=title, content=content, wait=True,
        )
    await params.result_callback({"status": "synced", "notebook_id": notebook_id, "title": title})


def build_tools(
    builtin_tools: list[str], output_dir: str, recorder: TranscriptRecorder,
) -> list[FunctionSchema]:
    output_path = Path(output_dir).resolve()

    async def web_read_handler(params: FunctionCallParams):
        from tavily import AsyncTavilyClient

        url = params.arguments["url"]
        logger.info(f"WebRead: {url}")
        client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = await client.extract(urls=[url])
        results = response.get("results", [])
        content = results[0]["raw_content"][:5000] if results else "Failed to extract content"
        await params.result_callback({"url": url, "content": content})

    async def file_read_handler(params: FunctionCallParams):
        filename = params.arguments["filename"]
        path = safe_resolve(output_path, filename)
        if not path:
            await params.result_callback({"error": "Access denied: path outside output directory"})
            return
        if not path.exists():
            await params.result_callback({"error": f"File not found: {filename}"})
            return
        await params.result_callback({"filename": filename, "content": path.read_text()[:5000]})

    async def file_write_handler(params: FunctionCallParams):
        filename = params.arguments["filename"]
        content = params.arguments["content"]
        path = safe_resolve(output_path, filename)
        if not path:
            await params.result_callback({"error": "Access denied: path outside output directory"})
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        logger.info(f"File written: {path}")
        await params.result_callback({"status": "saved", "path": str(path), "content": content[:3000]})

    async def file_list_handler(params: FunctionCallParams):
        files = sorted(output_path.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        entries = [{"name": f.name, "size": f.stat().st_size} for f in files[:20]]
        await params.result_callback({"directory": str(output_path), "files": entries})

    async def summarize_handler(params: FunctionCallParams):
        from google import genai

        transcript = recorder.get_transcript_text()
        if not transcript:
            await params.result_callback({"error": "No transcript recorded yet"})
            return
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        response = await client.aio.models.generate_content(
            model="gemini-3.7-flash",
            contents=f"Summarize this conversation transcript into markdown with these sections:\n"
            f"## Key Ideas\n## Decisions Made\n## Action Items\n## Open Questions\n\n"
            f"Be concise. Use bullet points.\n\nTranscript:\n{transcript[:10000]}",
        )
        summary = response.text[:5000]
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}-session-summary.md"
        filepath = output_path / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(summary)
        logger.info(f"Session summary saved to {filepath}")
        await params.result_callback({"status": "saved", "path": str(filepath), "content": summary[:500]})

    available = {}

    if os.environ.get("TAVILY_API_KEY"):
        available["websearch"] = FunctionSchema(
            name="web_search",
            description="Search the web for real-time information, documentation, or any topic",
            properties={"query": {"type": "string", "description": "Search query"}},
            required=["query"], handler=web_search_handler,
        )
        available["web_read"] = FunctionSchema(
            name="web_read",
            description="Read and extract the full content of a web page given its URL",
            properties={"url": {"type": "string", "description": "URL to read"}},
            required=["url"], handler=web_read_handler,
        )

    available["file_read"] = FunctionSchema(
        name="file_read",
        description="Read a file from the session output directory (past transcripts, notes)",
        properties={"filename": {"type": "string", "description": "Name of the file to read"}},
        required=["filename"], handler=file_read_handler,
    )
    available["file_write"] = FunctionSchema(
        name="file_write",
        description="Save content to a file in the session output directory",
        properties={
            "filename": {"type": "string", "description": "Name of the file to save"},
            "content": {"type": "string", "description": "Content to write"},
        },
        required=["filename", "content"], handler=file_write_handler,
    )
    available["file_list"] = FunctionSchema(
        name="file_list",
        description="List files in the session output directory",
        properties={}, required=[], handler=file_list_handler,
    )
    available["summarize_session"] = FunctionSchema(
        name="summarize_session",
        description="Get the current session transcript for summarization. Summarize into: Key Ideas, Decisions Made, Action Items, and Open Questions",
        properties={}, required=[], handler=summarize_handler,
    )
    available["get_current_time"] = FunctionSchema(
        name="get_current_time",
        description="Get the current date and time",
        properties={}, required=[], handler=get_current_time_handler,
    )
    available["deep_analysis"] = FunctionSchema(
        name="deep_analysis",
        description="Send a complex question to a powerful reasoning model for deep analysis. Use for root cause analysis, complex troubleshooting, or when you need thorough reasoning",
        properties={
            "query": {"type": "string", "description": "The question or analysis request"},
            "context": {"type": "string", "description": "Supporting context (case details, logs, error messages)"},
        },
        required=["query"], handler=deep_analysis_handler,
    )
    if os.environ.get("TAVILY_API_KEY"):
        available["research"] = FunctionSchema(
            name="research",
            description="Research a topic thoroughly: search the web, read top sources, and synthesize a structured report with Key Findings, Details, Sources, and Open Questions. Takes 10-15 seconds.",
            properties={
                "topic": {"type": "string", "description": "The topic or question to research"},
            },
            required=["topic"], handler=research_handler,
        )

    if os.environ.get("NOTEBOOKLM_NOTEBOOK_ID"):
        available["notebooklm_sync"] = FunctionSchema(
            name="notebooklm_sync",
            description="Sync a document to Google NotebookLM as a text source. Use for archiving case reports, research findings, or session summaries to the knowledge base.",
            properties={
                "title": {"type": "string", "description": "Title of the document"},
                "content": {"type": "string", "description": "Full markdown content to sync"},
            },
            required=["title", "content"], handler=notebooklm_sync_handler,
        )

    tools = []
    for name in builtin_tools:
        if name in available:
            tools.append(available[name])
            logger.info(f"Tool registered: {name}")
        else:
            logger.warning(f"Tool not available: {name} (missing API key or not implemented)")
    return tools
