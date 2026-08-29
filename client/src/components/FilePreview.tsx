import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Props {
  selected: { persona: string; filename: string } | null;
  onSelect?: (persona: string, filename: string) => void;
  onDeleted?: () => void;
  refreshKey?: number;
}

export function FilePreview({ selected, onSelect, onDeleted, refreshKey }: Props) {
  const [content, setContent] = useState("");
  const [raw, setRaw] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameTo, setRenameTo] = useState("");
  const renameRef = useRef<HTMLInputElement>(null);

  const isNlm = selected?.persona === "__nlm__";

  useEffect(() => {
    if (!selected) return;
    setRaw(false);
    setConfirmDelete(false);
    setRenaming(false);
    const url = isNlm
      ? `/api/notebooklm/sources/${selected.filename}`
      : `/api/files/${selected.filename}?persona=${selected.persona}`;
    fetch(url)
      .then((r) => r.json())
      .then((d) => setContent(d.content || d.error || ""));
  }, [selected?.persona, selected?.filename, refreshKey]);

  useEffect(() => {
    if (renaming && renameRef.current) renameRef.current.focus();
  }, [renaming]);

  const doRename = () => {
    if (!selected || !renameTo.trim() || isNlm) return;
    const name = renameTo.trim();
    fetch(
      `/api/files/${selected.filename}/rename?persona=${selected.persona}&new_name=${encodeURIComponent(name)}`,
      { method: "POST" },
    )
      .then((r) => r.json())
      .then((d) => {
        setRenaming(false);
        if (d.filename && onSelect) onSelect(selected.persona, d.filename);
        if (onDeleted) onDeleted();
      });
  };

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
        {renaming ? (
          <input
            ref={renameRef}
            className="rename-input"
            value={renameTo}
            onChange={(e) => setRenameTo(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") doRename();
              if (e.key === "Escape") setRenaming(false);
            }}
            onBlur={() => setRenaming(false)}
          />
        ) : (
          <span
            className={`doc-header-name ${!isNlm ? "pane-meta-interactive" : ""}`}
            title={!isNlm ? "Click to rename" : undefined}
            onClick={() => {
              if (isNlm) return;
              setRenameTo(selected.filename.replace(/\.(md|txt)$/, ""));
              setRenaming(true);
            }}
          >
            {selected.filename}
          </span>
        )}
        <div className="doc-header-meta">
          <span className="pane-meta" style={{ gap: 10 }}>
            {!isNlm && (
              <span
                className="pane-meta-interactive"
                style={confirmDelete ? { color: "var(--danger)" } : undefined}
                onClick={() => {
                  if (!confirmDelete) {
                    setConfirmDelete(true);
                    setTimeout(() => setConfirmDelete(false), 3000);
                    return;
                  }
                  fetch(
                    `/api/files/${selected.filename}?persona=${selected.persona}`,
                    { method: "DELETE" },
                  )
                    .then((r) => r.json())
                    .then((d) => {
                      if (d.deleted) {
                        setConfirmDelete(false);
                        if (onSelect) onSelect("", "");
                        if (onDeleted) onDeleted();
                      }
                    });
                }}
              >
                {confirmDelete ? "CONFIRM?" : "DELETE"}
              </span>
            )}
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
