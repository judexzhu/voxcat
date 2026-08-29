from datetime import datetime
from pathlib import Path


class TranscriptRecorder:
    def __init__(self, output_dir: str):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._turns: list[dict] = []
        self._session_start = datetime.now()
        self._topic = "untitled"

    def add_turn(self, role: str, content: str, timestamp: datetime | None = None):
        self._turns.append({
            "role": role,
            "content": content,
            "timestamp": timestamp or datetime.now(),
        })

    def set_topic(self, topic: str):
        self._topic = topic

    def save_transcript(self) -> Path:
        date_str = self._session_start.strftime("%Y-%m-%d")
        slug = self._topic.lower().replace(" ", "-")[:40]
        filename = f"{date_str}-{slug}.md"
        filepath = self._output_dir / filename

        duration = datetime.now() - self._session_start
        minutes = int(duration.total_seconds() // 60)

        lines = [
            f"# Brainstorm: {self._topic}",
            f"**Date:** {date_str}  |  **Duration:** {minutes}m",
            "",
            "## Key Ideas",
            "- *(review transcript below and fill in)*",
            "",
            "## Decisions Made",
            "- *(review transcript below and fill in)*",
            "",
            "## Action Items",
            "- [ ] *(review transcript below and fill in)*",
            "",
            "## Open Questions",
            "- *(review transcript below and fill in)*",
            "",
            "## Raw Transcript",
            "",
        ]

        for turn in self._turns:
            ts = turn["timestamp"]
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%H:%M:%S")
            role = turn["role"].capitalize()
            lines.append(f"**[{ts}] {role}:** {turn['content']}")
            lines.append("")

        filepath.write_text("\n".join(lines))
        return filepath

    def get_transcript_text(self) -> str:
        lines = []
        for turn in self._turns:
            ts = turn["timestamp"]
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%H:%M:%S")
            lines.append(f"[{ts}] {turn['role'].capitalize()}: {turn['content']}")
        return "\n".join(lines)
