"""Load persona profiles from markdown files or config.yaml fallback.

Persona files use YAML frontmatter + markdown body for the instruction:

    ---
    label: "Thinking Partner"
    description: "Probing questions, challenged assumptions."
    greeting: "What's on your mind?"
    voice:
      tts_voice: "Aoede"
      tts_style: "extremely fast"
    tools:
      builtin: [websearch, web_read, file_read, ...]
      mcp_servers: []
    output:
      directory: "output/thinking-partner"
    ---

    You are a brainstorming partner. Under 50 words per response...
"""

from pathlib import Path

import yaml
from loguru import logger


def _parse_persona_file(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"Persona file {path} missing YAML frontmatter")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Persona file {path} has unclosed frontmatter")

    frontmatter = yaml.safe_load(parts[1]) or {}
    instruction = parts[2].strip()
    frontmatter["instruction"] = instruction
    return frontmatter


def load_personas(personas_dir: Path | None, config: dict) -> dict[str, dict]:
    """Load personas from directory if it exists, fall back to config.yaml profiles.

    Returns dict of {slug: profile}.
    """
    profiles = {}

    if personas_dir and personas_dir.is_dir():
        for path in sorted(personas_dir.glob("*.md")):
            if path.name.startswith("_"):
                continue
            slug = path.stem
            try:
                profile = _parse_persona_file(path)
                profiles[slug] = profile
                logger.info(f"Persona loaded from file: {slug}")
            except Exception as e:
                logger.error(f"Failed to load persona {path}: {e}")

    if profiles:
        config_profiles = config.get("persona", {}).get("profiles", {})
        for slug in config_profiles:
            if slug not in profiles:
                profiles[slug] = config_profiles[slug]
                logger.info(f"Persona loaded from config: {slug}")
        return profiles

    return config.get("persona", {}).get("profiles", {})
