import { useCallback, useEffect, useState } from "react";

interface FileInfo {
  name: string;
  size: number;
  modified: number;
}

interface FolderNode {
  persona: string;
  label: string;
  files: FileInfo[];
}

interface NlmSource {
  id: string;
  title: string;
}

interface Props {
  persona: string;
  selected: { persona: string; filename: string } | null;
  onSelect: (persona: string, filename: string) => void;
}

export function OutputTree({ persona, selected, onSelect }: Props) {
  const [tree, setTree] = useState<FolderNode[]>([]);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [nlmSources, setNlmSources] = useState<NlmSource[]>([]);
  const [nlmTitle, setNlmTitle] = useState("NOTEBOOKLM");

  const toggle = (key: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const refresh = useCallback(() => {
    fetch("/api/files/tree")
      .then((r) => r.json())
      .then((d) => setTree(d.tree || []));
    fetch("/api/notebooklm/sources")
      .then((r) => r.json())
      .then((d) => {
        setNlmSources(d.sources || []);
        if (d.notebook_title) setNlmTitle(d.notebook_title);
      })
      .catch(() => setNlmSources([]));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const totalFiles = tree.reduce((n, f) => n + f.files.length, 0);

  return (
    <div className="pane output-pane">
      <div className="pane-header pane-header-output">
        <span className="pane-label">OUTPUT</span>
        <button className="output-refresh" onClick={refresh}>
          ↻
        </button>
      </div>
      <div className="output-scroll vx-scroll">
        {tree.map((folder, fi) => {
          const isCollapsed = collapsed.has(folder.persona);
          return (
            <div key={folder.persona}>
              <div
                className="output-group-header output-group-toggle"
                style={fi > 0 ? { paddingTop: 6 } : undefined}
                onClick={() => toggle(folder.persona)}
              >
                <span>
                  <span className="output-chevron">
                    {isCollapsed ? "▸" : "▾"}
                  </span>
                  {folder.persona.toUpperCase()}
                </span>
                <span className="output-group-count">
                  {folder.files.length}
                </span>
              </div>
              {!isCollapsed &&
                (folder.files.length === 0 ? (
                  <div className="output-empty">empty</div>
                ) : (
                  folder.files.map((f) => (
                    <div
                      key={f.name}
                      className={`output-file ${
                        selected?.persona === folder.persona &&
                        selected?.filename === f.name
                          ? "active"
                          : ""
                      }`}
                      onClick={() => onSelect(folder.persona, f.name)}
                    >
                      {f.name}
                    </div>
                  ))
                ))}
            </div>
          );
        })}

        {nlmSources.length > 0 && (
          <div>
            <div
              className="output-group-header output-group-toggle"
              style={{ paddingTop: 6 }}
              onClick={() => toggle("__nlm__")}
            >
              <span>
                <span className="output-chevron">
                  {collapsed.has("__nlm__") ? "▸" : "▾"}
                </span>
                {nlmTitle.toUpperCase()} <span style={{ color: "var(--text-5)", fontSize: "9px" }}>NLM</span>
              </span>
              <span className="output-group-count">{nlmSources.length}</span>
            </div>
            {!collapsed.has("__nlm__") &&
              nlmSources.map((s) => (
                <div
                  key={s.id}
                  className={`output-file ${
                    selected?.persona === "__nlm__" &&
                    selected?.filename === s.id
                      ? "active"
                      : ""
                  }`}
                  onClick={() => onSelect("__nlm__", s.id)}
                >
                  {s.title}
                </div>
              ))}
          </div>
        )}
      </div>
      <div className="output-footer">
        {totalFiles} FILES · {tree.length} ROOTS
        {nlmSources.length > 0 && ` · ${nlmSources.length} NLM`}
      </div>
    </div>
  );
}
