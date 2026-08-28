import { useCallback, useEffect, useState } from "react";
import Markdown from "react-markdown";

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

export function FileExplorer({ persona }: { persona: string }) {
  const [tree, setTree] = useState<FolderNode[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<{
    persona: string;
    filename: string;
  } | null>(null);
  const [content, setContent] = useState("");

  const refresh = useCallback(() => {
    fetch("/api/files/tree")
      .then((r) => r.json())
      .then((d) => {
        setTree(d.tree || []);
        setExpanded(new Set([persona]));
      });
  }, [persona]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const toggleFolder = (name: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const openFile = (p: string, filename: string) => {
    setSelected({ persona: p, filename });
    fetch(`/api/files/${filename}?persona=${p}`)
      .then((r) => r.json())
      .then((d) => setContent(d.content || d.error || ""));
  };

  return (
    <div className="file-explorer-split">
      <div className="file-tree">
        <div className="file-tree-header">
          <span>Explorer</span>
          <button className="refresh-btn" onClick={refresh}>
            ↻
          </button>
        </div>
        <div className="file-tree-content">
          {tree.map((folder) => (
            <div key={folder.persona} className="tree-folder">
              <div
                className="tree-folder-name"
                onClick={() => toggleFolder(folder.persona)}
              >
                <span className="tree-chevron">
                  {expanded.has(folder.persona) ? "▾" : "▸"}
                </span>
                {folder.label}
                <span className="tree-count">{folder.files.length}</span>
              </div>
              {expanded.has(folder.persona) &&
                folder.files.map((f) => (
                  <div
                    key={f.name}
                    className={`tree-file ${
                      selected?.persona === folder.persona &&
                      selected?.filename === f.name
                        ? "active"
                        : ""
                    }`}
                    onClick={() => openFile(folder.persona, f.name)}
                  >
                    {f.name}
                  </div>
                ))}
              {expanded.has(folder.persona) && folder.files.length === 0 && (
                <div className="tree-empty">No files</div>
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="file-preview">
        {selected ? (
          <>
            <div className="file-preview-header">{selected.filename}</div>
            <div className="file-preview-content">
              <Markdown>{content}</Markdown>
            </div>
          </>
        ) : (
          <div className="file-preview-empty">Select a file to preview</div>
        )}
      </div>
    </div>
  );
}
