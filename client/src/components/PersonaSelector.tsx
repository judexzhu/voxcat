import { useEffect, useState } from "react";

interface PersonaInfo {
  name: string;
  label: string;
  description: string;
}

interface FileCount {
  persona: string;
  count: number;
  dir: string;
}

interface Props {
  value: string;
  onChange: (persona: string) => void;
}

export function PersonaSelector({ value, onChange }: Props) {
  const [personas, setPersonas] = useState<PersonaInfo[]>([]);
  const [fileCounts, setFileCounts] = useState<Record<string, FileCount>>({});

  useEffect(() => {
    fetch("/api/personas")
      .then((r) => r.json())
      .then((data) => {
        setPersonas(data.personas);
        if (!value) onChange(data.default);
      });
    fetch("/api/files/tree")
      .then((r) => r.json())
      .then((data) => {
        const counts: Record<string, FileCount> = {};
        for (const folder of data.tree || []) {
          counts[folder.persona] = {
            persona: folder.persona,
            count: folder.files?.length || 0,
            dir: folder.persona + "/",
          };
        }
        setFileCounts(counts);
      });
  }, []);

  return (
    <div className="persona-list">
      {personas.map((p) => (
        <div
          key={p.name}
          className={`persona-row ${value === p.name ? "selected" : ""}`}
          onClick={() => onChange(p.name)}
        >
          <div className="persona-row-left">
            <div className="persona-name-row">
              <div className="persona-dot" />
              <span className="persona-name">{p.label}</span>
            </div>
            <span className="persona-desc">{p.description}</span>
          </div>
          <div className="persona-row-right">
            {value === p.name && (
              <span className="persona-selected-label">SELECTED</span>
            )}
            <span className="persona-meta">
              {fileCounts[p.name]
                ? `${fileCounts[p.name].dir} · ${fileCounts[p.name].count}`
                : ""}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
