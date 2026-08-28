import { useEffect, useState } from "react";

const PERSONA_LABELS: Record<string, string> = {
  "thinking-partner": "Thinking Partner",
  "devils-advocate": "Devil's Advocate",
  "note-taker": "Note Taker",
  sre: "SRE Assistant",
};

interface Props {
  value: string;
  onChange: (persona: string) => void;
  disabled?: boolean;
}

export function PersonaSelector({ value, onChange, disabled }: Props) {
  const [personas, setPersonas] = useState<string[]>([]);

  useEffect(() => {
    fetch("/api/personas")
      .then((r) => r.json())
      .then((data) => {
        setPersonas(data.personas);
        if (!value) onChange(data.default);
      });
  }, []);

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="persona-selector"
    >
      {personas.map((p) => (
        <option key={p} value={p}>
          {PERSONA_LABELS[p] || p}
        </option>
      ))}
    </select>
  );
}
