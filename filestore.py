from pathlib import Path


def safe_resolve(base_dir: Path, filename: str) -> Path | None:
    """Resolve filename under base_dir, return None if path escapes."""
    base = base_dir.resolve()
    path = (base / filename).resolve()
    if not str(path).startswith(str(base)):
        return None
    return path
