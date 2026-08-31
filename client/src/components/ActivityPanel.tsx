import { useEffect, useRef, useState } from "react";
import Markdown from "react-markdown";
import type { ActivityEntry } from "../types";
import { ToolResultCard } from "./ToolResultCard";

interface Props {
  entries: ActivityEntry[];
  speaking: boolean;
  onFileClick?: (filename: string) => void;
  onSendText?: (text: string) => void;
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

export function ActivityPanel({ entries, speaking, onFileClick, onSendText }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const userScrolledRef = useRef(false);
  const [toolsOnly, setToolsOnly] = useState(false);
  const [textInput, setTextInput] = useState("");

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
      userScrolledRef.current = !atBottom;
    };
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && !userScrolledRef.current) {
      el.scrollTop = el.scrollHeight;
    }
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
                  <div className="timeline-utterance"><Markdown components={{a: ({children, ...props}) => <a {...props} target="_blank" rel="noopener noreferrer">{children}</a>}}>{entry.text}</Markdown></div>
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
      {onSendText && (
        <div className="timeline-input">
          <input
            type="text"
            className="timeline-input-field"
            placeholder="Type a message..."
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && textInput.trim()) {
                onSendText(textInput.trim());
                setTextInput("");
              }
            }}
          />
          <button
            className="timeline-send-btn"
            onClick={() => {
              if (textInput.trim()) {
                onSendText(textInput.trim());
                setTextInput("");
              }
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
