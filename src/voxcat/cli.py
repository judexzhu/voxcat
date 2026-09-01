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

    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_level = args.log_level

    env_path = CONFIG_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)
    load_dotenv(override=True)

    from .bot import load_config, set_config
    from .personas import load_personas

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
    if not personas_dir.is_dir():
        try:
            pkg_personas = Path(str(resources.files("voxcat") / "personas"))
            if pkg_personas.is_dir():
                personas_dir = pkg_personas
        except (TypeError, FileNotFoundError):
            pass
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

    sessions_dir = DATA_DIR / "sessions"
    config["sessions_dir"] = str(sessions_dir)

    # Make config available to bot.run_bot() when called by pipecat runner
    set_config(config)

    from fastapi.staticfiles import StaticFiles
    from pipecat.runner.run import app, main as pipecat_main

    # pipecat import adds its own loguru handler — reset to ours with filter
    logger.remove()
    logger.add(sys.stderr, filter=_not_prebuilt)
    logger.add(
        log_dir / "voxcat_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level=log_level,
        format="{time:HH:mm:ss.SSS} | {level:<7} | {name}:{function}:{line} | {message}",
        filter=_not_prebuilt,
    )
    logger.info(f"Logs: {log_dir}")

    from .api import register_routes

    sessions_dir = Path(config["sessions_dir"])
    register_routes(app, config, available_personas, sessions_dir)

    client_dist = get_client_dist()
    if client_dist:
        app.mount("/client", StaticFiles(directory=str(client_dist), html=True))

        from fastapi.responses import RedirectResponse

        @app.get("/", include_in_schema=False)
        async def root_redirect():
            return RedirectResponse(url="/client/")

    pipecat_main()
