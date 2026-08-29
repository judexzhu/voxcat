import argparse
import os
import shutil
import sys
from importlib import resources
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


def get_client_dist() -> Path | None:
    cwd_dist = Path.cwd() / "client" / "dist"
    if cwd_dist.is_dir():
        return cwd_dist
    try:
        pkg = resources.files("voxcat") / "client" / "dist"
        if pkg.is_dir():
            return Path(str(pkg))
    except (TypeError, FileNotFoundError):
        pass
    return None


def init_project(target: Path):
    """Copy default config and .env templates to target directory."""
    pkg = resources.files("voxcat")
    for name in ("config.yaml.example", ".env.example"):
        src = pkg / name
        dest_name = name.replace(".example", "") if name != "config.yaml.example" else name
        dest = target / dest_name
        if name == "config.yaml.example":
            dest = target / "config.yaml"
            if dest.exists():
                print(f"  skip {dest} (already exists)")
                continue
            dest.write_text(src.read_text())
            print(f"  created {dest}")
        else:
            dest = target / ".env"
            if dest.exists():
                print(f"  skip {dest} (already exists)")
                continue
            dest.write_text(src.read_text())
            print(f"  created {dest}")
    print("\nEdit .env with your API keys, then run: voxcat")


def main():
    parser = argparse.ArgumentParser(description="Voxcat — voice AI agent with swappable personas")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--port", type=int, default=None, help="Server port (overrides config)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="Create config.yaml and .env in the current directory")
    args = parser.parse_args()

    if args.command == "init":
        init_project(Path.cwd())
        return

    load_dotenv(override=True)

    from .bot import load_config
    from .filestore import safe_resolve
    from .transcript import SESSIONS_DIR

    # pipecat runner discovers bot() via sys.modules["__main__"]
    import sys
    from .bot import bot as _bot_func
    sys.modules["__main__"].bot = _bot_func

    config_path = args.config or Path.cwd() / "config.yaml"
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        print("Run 'voxcat init' to create one, or use --config path/to/config.yaml")
        sys.exit(1)

    config = load_config(config_path)
    available_personas = list(config["persona"]["profiles"].keys())

    if args.port:
        config.setdefault("server", {})["port"] = args.port

    from fastapi.staticfiles import StaticFiles
    from pipecat.runner.run import app, main as pipecat_main

    @app.get("/api/personas")
    async def list_personas():
        return {"personas": available_personas, "default": config["persona"]["default"]}

    @app.get("/api/files/tree")
    async def file_tree():
        tree = []
        for name in available_personas:
            profile = config["persona"]["profiles"][name]
            output_dir = Path(profile.get("output", {}).get("directory", f"output/{name}"))
            output_dir.mkdir(parents=True, exist_ok=True)
            files = sorted(output_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
            tree.append({
                "persona": name,
                "label": {"thinking-partner": "Thinking Partner", "devils-advocate": "Devil's Advocate",
                          "note-taker": "Note Taker", "sre": "SRE Assistant"}.get(name, name),
                "files": [
                    {"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
                    for f in files[:50] if f.is_file()
                ],
            })
        return {"tree": tree}

    @app.get("/api/files")
    async def list_files(persona: str = "thinking-partner"):
        profile = config["persona"]["profiles"].get(persona, {})
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms"))
        output_dir.mkdir(parents=True, exist_ok=True)
        files = sorted(output_dir.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        return {
            "directory": str(output_dir),
            "files": [
                {"name": f.name, "size": f.stat().st_size, "modified": f.stat().st_mtime}
                for f in files[:50] if f.is_file()
            ],
        }

    @app.get("/api/files/{filename:path}")
    async def read_file(filename: str, persona: str = "thinking-partner"):
        profile = config["persona"]["profiles"].get(persona, {})
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms"))
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        return {"filename": filename, "content": path.read_text()[:10000]}

    @app.delete("/api/files/{filename:path}")
    async def delete_file(filename: str, persona: str = "thinking-partner"):
        profile = config["persona"]["profiles"].get(persona, {})
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms"))
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        path.unlink()
        return {"deleted": filename}

    @app.post("/api/files/{filename:path}/rename")
    async def rename_file(filename: str, new_name: str, persona: str = "thinking-partner"):
        profile = config["persona"]["profiles"].get(persona, {})
        output_dir = Path(profile.get("output", {}).get("directory", "brainstorms"))
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
        if SESSIONS_DIR.is_dir():
            for persona_dir in sorted(SESSIONS_DIR.iterdir()):
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
        path = safe_resolve(SESSIONS_DIR / persona, filename)
        if not path or not path.exists():
            return {"error": "Session not found"}
        return {"content": path.read_text()[:20000], "persona": persona, "filename": filename}

    @app.delete("/api/sessions/{persona}/{filename}")
    async def delete_session(persona: str, filename: str):
        path = safe_resolve(SESSIONS_DIR / persona, filename)
        if not path or not path.exists():
            return {"error": "Session not found"}
        path.unlink()
        return {"deleted": filename}

    @app.post("/api/sessions/{persona}/{filename}/rename")
    async def rename_session(persona: str, filename: str, new_name: str):
        path = safe_resolve(SESSIONS_DIR / persona, filename)
        if not path or not path.exists():
            return {"error": "Session not found"}
        if not new_name.endswith(".md"):
            new_name += ".md"
        new_path = safe_resolve(SESSIONS_DIR / persona, new_name)
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
                sources = await client.sources.list(notebook_id)
                return {"sources": [
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

    client_dist = get_client_dist()
    if client_dist:
        app.mount("/client", StaticFiles(directory=str(client_dist), html=True))

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/client/")

    pipecat_main()
