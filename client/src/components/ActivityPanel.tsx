import { useEffect, useRef } from "react";
import type { ActivityEntry } from "../types";
import { ToolResultCard } from "./ToolResultCard";

interface Props {
  entries: ActivityEntry[];
}

export function ActivityPanel({ entries }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  return (
    <div className="activity-panel">
      <div className="activity-header">Activity</div>
      <div className="activity-entries">
        {entries.map((entry, i) => {
          switch (entry.kind) {
            case "user":
              return (
                <div key={i} className="entry entry-user">
                  <span className="role">You:</span> {entry.text}
                </div>
              );
            case "bot":
              return (
                <div key={i} className="entry entry-bot">
                  <span className="role">Voxcat:</span> {entry.text}
                </div>
              );
            case "tool-start":
              return (
                <div key={i} className="entry entry-tool-start">
                  ⚙️ Calling <strong>{entry.functionName}</strong>...
                </div>
              );
            case "tool-result":
              return (
                <div key={i} className="entry entry-tool-result">
                  <ToolResultCard
                    functionName={entry.functionName}
                    result={entry.result}
                    cancelled={entry.cancelled}
                  />
                </div>
              );
          }
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
