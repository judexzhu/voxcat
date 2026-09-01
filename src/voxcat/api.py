"""REST API routes for file, session, persona, and NotebookLM endpoints."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from loguru import logger

from .filestore import safe_resolve


def _persona_dir(config: dict, persona: str) -> Path:
    profile = config["persona"]["profiles"].get(persona)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Unknown persona: {persona}")
    return Path(profile.get("output", {}).get("directory", f"output/{persona}"))


def _persona_label(config: dict, name: str) -> str:
    return config["persona"]["profiles"][name].get("label", name.replace("-", " ").title())


def _list_files(directory: Path, limit: int = 50) -> list[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (f for f in directory.glob("*") if f.is_file() and not f.name.startswith(".")),
        key=lambda f: f.stat().st_mtime, reverse=True,
    )
    return [
        {"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
        for f in files[:limit]
    ]


def register_routes(app: FastAPI, config: dict, available_personas: list[str], sessions_dir: Path):
    """Register all REST API routes on the given FastAPI app."""

    @app.get("/api/personas")
    async def list_personas():
        personas = []
        for name in available_personas:
            profile = config["persona"]["profiles"][name]
            personas.append({
                "name": name,
                "label": _persona_label(config, name),
                "description": profile.get("description", ""),
            })
        return {"personas": personas, "default": config["persona"]["default"]}

    @app.get("/api/files/tree")
    async def file_tree():
        tree = []
        for name in available_personas:
            output_dir = _persona_dir(config, name)
            tree.append({
                "persona": name,
                "label": _persona_label(config, name),
                "files": _list_files(output_dir),
            })
        return {"tree": tree}

    @app.get("/api/files")
    async def list_files(persona: str = "thinking-partner"):
        output_dir = _persona_dir(config, persona)
        return {"directory": str(output_dir), "files": _list_files(output_dir)}

    @app.get("/api/files/{filename:path}")
    async def read_file(filename: str, persona: str = "thinking-partner"):
        output_dir = _persona_dir(config, persona)
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        try:
            return {"filename": filename, "content": path.read_text()[:10000]}
        except UnicodeDecodeError:
            return {"error": "Binary file, cannot display"}

    @app.delete("/api/files/{filename:path}")
    async def delete_file(filename: str, persona: str = "thinking-partner"):
        output_dir = _persona_dir(config, persona)
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        path.unlink()
        return {"deleted": filename}

    @app.post("/api/files/{filename:path}/rename")
    async def rename_file(filename: str, new_name: str, persona: str = "thinking-partner"):
        output_dir = _persona_dir(config, persona)
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        if not new_name.endswith(".md") and not new_name.endswith(".txt"):
            new_name += ".md"
        new_path = safe_resolve(output_dir, new_name)
        if not new_path:
            return {"error": "Invalid name"}
        path.rename(new_path)
        return {"filename": new_name}

    @app.get("/api/sessions")
    async def list_sessions():
        sessions = []
        if sessions_dir.is_dir():
            for persona_dir in sorted(sessions_dir.iterdir()):
                if not persona_dir.is_dir():
                    continue
                files = sorted(persona_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
                for f in files[:20]:
                    sessions.append({
                        "persona": persona_dir.name,
                        "filename": f.name,
                        "modified": f.stat().st_mtime,
                    })
        sessions.sort(key=lambda s: s["modified"], reverse=True)
        return {"sessions": sessions}

    @app.get("/api/sessions/{persona}/{filename}")
    async def read_session(persona: str, filename: str):
        path = safe_resolve(sessions_dir / persona, filename)
        if not path or not path.exists():
            return {"error": "Session not found"}
        return {"content": path.read_text()[:20000], "persona": persona, "filename": filename}

    @app.delete("/api/sessions/{persona}/{filename}")
    async def delete_session(persona: str, filename: str):
        path = safe_resolve(sessions_dir / persona, filename)
        if not path or not path.exists():
            return {"error": "Session not found"}
        path.unlink()
        return {"deleted": filename}

    @app.post("/api/sessions/{persona}/{filename}/rename")
    async def rename_session(persona: str, filename: str, new_name: str):
        path = safe_resolve(sessions_dir / persona, filename)
        if not path or not path.exists():
            return {"error": "Session not found"}
        if not new_name.endswith(".md"):
            new_name += ".md"
        new_path = safe_resolve(sessions_dir / persona, new_name)
        if not new_path:
            return {"error": "Invalid name"}
        path.rename(new_path)
        return {"filename": new_name}

    notebook_id = os.environ.get("NOTEBOOKLM_NOTEBOOK_ID", "")

    @app.get("/api/notebooklm/sources")
    async def nlm_sources():
        if not notebook_id:
            return {"sources": []}
        try:
            from notebooklm import NotebookLMClient
            async with NotebookLMClient.from_storage() as client:
                meta = await client.notebooks.get_metadata(notebook_id)
                sources = await client.sources.list(notebook_id)
                return {"notebook_title": meta.title, "sources": [
                    {"id": s.id, "title": s.title}
                    for s in sources
                ]}
        except Exception as e:
            logger.error(f"NotebookLM sources error: {e}")
            return {"sources": []}

    @app.get("/api/notebooklm/sources/{source_id}")
    async def nlm_source_content(source_id: str):
        if not notebook_id:
            return {"error": "NotebookLM not configured"}
        try:
            from notebooklm import NotebookLMClient
            async with NotebookLMClient.from_storage() as client:
                fulltext = await client.sources.get_fulltext(notebook_id, source_id, output_format="markdown")
                return {"content": fulltext.content[:20000]}
        except Exception as e:
            logger.error(f"NotebookLM source read error: {e}")
            return {"error": str(e)}
