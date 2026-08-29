import { useEffect, useRef, useState } from "react";
import type { ActivityEntry } from "../types";
import { ToolResultCard } from "./ToolResultCard";

interface Props {
  entries: ActivityEntry[];
  speaking: boolean;
  onFileClick?: (filename: string) => void;
}

function formatTime(ts: number): string {
  const d = new Date(ts);
  return [d.getHours(), d.getMinutes(), d.getSeconds()]
    .map((n) => String(n).padStart(2, "0"))
    .join(":");
}

function findLatency(
  entry: ActivityEntry & { kind: "tool-result" },
  entries: ActivityEntry[],
): number | undefined {
  for (let i = entries.length - 1; i >= 0; i--) {
    const e = entries[i];
    if (e.kind === "tool-start" && e.toolCallId === entry.toolCallId) {
      return entry.timestamp - e.timestamp;
    }
  }
  return undefined;
}

export function ActivityPanel({ entries, speaking, onFileClick }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [toolsOnly, setToolsOnly] = useState(false);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  });

  const visible = toolsOnly
    ? entries.filter((e) => e.kind === "tool-start" || e.kind === "tool-result")
    : entries;

  const isStreaming = speaking;

  return (
    <div className="pane">
      <div className="pane-header pane-header-timeline">
        <span className="pane-label">TIMELINE</span>
        <div className="pane-meta">
          <span>{entries.length} EVENTS</span>
          <span
            className="pane-meta-interactive"
            onClick={() => setToolsOnly(!toolsOnly)}
            style={toolsOnly ? { color: "var(--accent-text)" } : undefined}
          >
            TOOLS ONLY
          </span>
        </div>
      </div>
      <div className="timeline-scroll vx-scroll" ref={scrollRef}>
        {visible.map((entry, i) => {
          if (entry.kind === "user") {
            return (
              <div key={i} className="timeline-row">
                <div className="timeline-ts">{formatTime(entry.timestamp)}</div>
                <div className="timeline-body">
                  <div className="timeline-speaker timeline-speaker-you">YOU</div>
                  <div className="timeline-utterance">{entry.text}</div>
                </div>
              </div>
            );
          }

          if (entry.kind === "bot") {
            const streaming = isStreaming && i === visible.length - 1;
            return (
              <div key={i} className="timeline-row">
                <div className="timeline-ts">{formatTime(entry.timestamp)}</div>
                <div className="timeline-body">
                  <div className="timeline-speaker timeline-speaker-bot">
                    VOXCAT
                  </div>
                  <div className="timeline-utterance">{entry.text}</div>
                  {streaming && (
                    <div className="timeline-speaking">
                      <div className="timeline-speaking-track">
                        <div className="timeline-speaking-bar" />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          }

          if (entry.kind === "tool-start") {
            return (
              <div key={i} className="timeline-row timeline-row-tool">
                <div className="timeline-ts">{formatTime(entry.timestamp)}</div>
                <div className="timeline-body timeline-body-tool">
                  <div className="tool-header">
                    <div className="tool-dot" />
                    <span className="tool-name">
                      {entry.functionName.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>
            );
          }

          if (entry.kind === "tool-result") {
            return (
              <div key={i} className="timeline-row timeline-row-tool">
                <div className="timeline-ts">{formatTime(entry.timestamp)}</div>
                <div className="timeline-body timeline-body-tool">
                  <ToolResultCard
                    functionName={entry.functionName}
                    result={entry.result}
                    cancelled={entry.cancelled}
                    latencyMs={findLatency(entry, entries)}
                    onFileClick={onFileClick}
                  />
                </div>
              </div>
            );
          }

          return null;
        })}
      </div>
    </div>
  );
}
