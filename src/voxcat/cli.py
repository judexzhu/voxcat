import argparse
import os
import sys
from importlib import resources
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Suppress pipecat's "prebuilt frontend not available" — we serve our own UI
def _not_prebuilt(record):
    return "pipecat_ai_prebuilt" not in record["message"]

logger.remove()
logger.add(sys.stderr, filter=_not_prebuilt)

CONFIG_DIR = Path.home() / ".config" / "voxcat"
DATA_DIR = Path.home() / "Documents" / "voxcat"


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


def init_project():
    """Create ~/.config/voxcat/ and ~/Documents/voxcat/ with defaults."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    pkg = resources.files("voxcat")

    config_dest = CONFIG_DIR / "config.yaml"
    if config_dest.exists():
        print(f"  skip {config_dest} (already exists)")
    else:
        config_dest.write_text((pkg / "config.yaml.example").read_text())
        print(f"  created {config_dest}")

    env_dest = CONFIG_DIR / ".env"
    if env_dest.exists():
        print(f"  skip {env_dest} (already exists)")
    else:
        env_dest.write_text((pkg / ".env.example").read_text())
        print(f"  created {env_dest}")

    personas_dest = CONFIG_DIR / "personas"
    if personas_dest.is_dir():
        print(f"  skip {personas_dest}/ (already exists)")
    else:
        import shutil
        pkg_personas = Path(str(pkg / "personas"))
        if pkg_personas.is_dir():
            shutil.copytree(str(pkg_personas), str(personas_dest))
            print(f"  created {personas_dest}/ ({len(list(personas_dest.glob('*.md')))} personas)")

    print(f"\nEdit {env_dest} with your API keys, then run: voxcat")


def main():
    parser = argparse.ArgumentParser(description="Voxcat — voice AI agent with swappable personas")
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml")
    parser.add_argument("--port", type=int, default=None, help="Server port (overrides config)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level (default: INFO)")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("init", help="Create config and env in ~/.config/voxcat/")
    args = parser.parse_args()

    if args.command == "init":
        init_project()
        return

    # Logging: file
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / "voxcat_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level=args.log_level,
        format="{time:HH:mm:ss.SSS} | {level:<7} | {name}:{function}:{line} | {message}",
        filter=_not_prebuilt,
    )
    logger.info(f"Logs: {log_dir}")

    env_path = CONFIG_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    load_dotenv(override=True)

    from .bot import load_config, set_config
    from .filestore import safe_resolve
    from .personas import load_personas
    from . import transcript

    # pipecat runner discovers bot() via sys.modules["__main__"]
    from .bot import bot as _bot_func
    sys.modules["__main__"].bot = _bot_func

    config_path = args.config
    if not config_path:
        if (CONFIG_DIR / "config.yaml").exists():
            config_path = CONFIG_DIR / "config.yaml"
        elif (Path.cwd() / "config.yaml").exists():
            config_path = Path.cwd() / "config.yaml"

    if not config_path or not config_path.exists():
        print(f"Config not found. Checked:")
        print(f"  {CONFIG_DIR / 'config.yaml'}")
        print(f"  {Path.cwd() / 'config.yaml'}")
        print("Run 'voxcat init' to create one, or use --config path/to/config.yaml")
        sys.exit(1)

    config = load_config(config_path)

    personas_dir = CONFIG_DIR / "personas"
    profiles = load_personas(personas_dir, config)
    config.setdefault("persona", {})["profiles"] = profiles
    available_personas = list(profiles.keys())

    if args.port:
        config.setdefault("server", {})["port"] = args.port

    # Resolve output dirs: make relative paths relative to DATA_DIR
    for name, profile in config["persona"]["profiles"].items():
        output_dir = profile.get("output", {}).get("directory", f"output/{name}")
        if not Path(output_dir).is_absolute():
            profile.setdefault("output", {})["directory"] = str(DATA_DIR / output_dir)

    # Sessions dir under DATA_DIR
    transcript.SESSIONS_DIR = DATA_DIR / "sessions"

    # Make config available to bot.run_bot() when called by pipecat runner
    set_config(config)

    from fastapi import HTTPException
    from fastapi.staticfiles import StaticFiles
    from pipecat.runner.run import app, main as pipecat_main

    def _persona_dir(persona: str) -> Path:
        profile = config["persona"]["profiles"].get(persona)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Unknown persona: {persona}")
        return Path(profile.get("output", {}).get("directory", f"output/{persona}"))

    def _persona_label(name: str) -> str:
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

    @app.get("/api/personas")
    async def list_personas():
        personas = []
        for name in available_personas:
            profile = config["persona"]["profiles"][name]
            personas.append({
                "name": name,
                "label": _persona_label(name),
                "description": profile.get("description", ""),
            })
        return {"personas": personas, "default": config["persona"]["default"]}

    @app.get("/api/files/tree")
    async def file_tree():
        tree = []
        for name in available_personas:
            output_dir = _persona_dir(name)
            tree.append({
                "persona": name,
                "label": _persona_label(name),
                "files": _list_files(output_dir),
            })
        return {"tree": tree}

    @app.get("/api/files")
    async def list_files(persona: str = "thinking-partner"):
        output_dir = _persona_dir(persona)
        return {"directory": str(output_dir), "files": _list_files(output_dir)}

    @app.get("/api/files/{filename:path}")
    async def read_file(filename: str, persona: str = "thinking-partner"):
        output_dir = _persona_dir(persona)
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        try:
            return {"filename": filename, "content": path.read_text()[:10000]}
        except UnicodeDecodeError:
            return {"error": "Binary file, cannot display"}

    @app.delete("/api/files/{filename:path}")
    async def delete_file(filename: str, persona: str = "thinking-partner"):
        output_dir = _persona_dir(persona)
        path = safe_resolve(output_dir, filename)
        if not path or not path.exists():
            return {"error": "File not found"}
        path.unlink()
        return {"deleted": filename}

    @app.post("/api/files/{filename:path}/rename")
    async def rename_file(filename: str, new_name: str, persona: str = "thinking-partner"):
        output_dir = _persona_dir(persona)
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

    sessions_dir = transcript.SESSIONS_DIR

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

    client_dist = get_client_dist()
    if client_dist:
        app.mount("/client", StaticFiles(directory=str(client_dist), html=True))

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/client/")

    pipecat_main()
