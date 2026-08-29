import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  selected: { persona: string; filename: string } | null;
}

export function FilePreview({ selected }: Props) {
  const [content, setContent] = useState("");
  const [raw, setRaw] = useState(false);

  useEffect(() => {
    if (!selected) return;
    setRaw(false);
    const url =
      selected.persona === "__nlm__"
        ? `/api/notebooklm/sources/${selected.filename}`
        : `/api/files/${selected.filename}?persona=${selected.persona}`;
    fetch(url)
      .then((r) => r.json())
      .then((d) => setContent(d.content || d.error || ""));
  }, [selected?.persona, selected?.filename]);

  if (!selected) {
    return (
      <div className="pane">
        <div className="pane-header pane-header-document">
          <span className="doc-header-name"></span>
        </div>
        <div className="doc-empty">Select a file to preview</div>
      </div>
    );
  }

  return (
    <div className="pane">
      <div className="pane-header pane-header-document">
        <span className="doc-header-name">{selected.filename}</span>
        <div className="doc-header-meta">
          <span className="pane-meta">
            <span
              className="pane-meta-interactive"
              onClick={() => setRaw(!raw)}
              style={raw ? { color: "var(--accent-text)" } : undefined}
            >
              RAW
            </span>
          </span>
        </div>
      </div>
      <div className="doc-scroll vx-scroll">
        {raw ? (
          <pre className="doc-raw">{content}</pre>
        ) : (
          <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
        )}
      </div>
    </div>
  );
}
