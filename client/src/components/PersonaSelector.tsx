import { useEffect, useState } from "react";

const PERSONA_LABELS: Record<string, string> = {
  "thinking-partner": "Thinking Partner",
  "devils-advocate": "Devil's Advocate",
  "note-taker": "Note Taker",
  sre: "SRE Assistant",
};

const PERSONA_DESCS: Record<string, string> = {
  "thinking-partner":
    "Probing questions, challenged assumptions, two sentences at a time.",
  "devils-advocate": "Takes the opposite side of whatever you just said.",
  "note-taker": "Stays quiet, writes down what you say.",
  sre: "Cases, KCS and Jira, read-only. Summarises findings.",
};

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
  const [personas, setPersonas] = useState<string[]>([]);
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
          key={p}
          className={`persona-row ${value === p ? "selected" : ""}`}
          onClick={() => onChange(p)}
        >
          <div className="persona-row-left">
            <div className="persona-name-row">
              <div className="persona-dot" />
              <span className="persona-name">
                {PERSONA_LABELS[p] || p}
              </span>
            </div>
            <span className="persona-desc">
              {PERSONA_DESCS[p] || ""}
            </span>
          </div>
          <div className="persona-row-right">
            {value === p && (
              <span className="persona-selected-label">SELECTED</span>
            )}
            <span className="persona-meta">
              {fileCounts[p]
                ? `${fileCounts[p].dir} · ${fileCounts[p].count}`
                : ""}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
