import { useEffect, useRef, useState } from "react";
import { PipecatAppBase } from "@pipecat-ai/voice-ui-kit";
import type { PipecatBaseChildProps } from "@pipecat-ai/voice-ui-kit";
import "@pipecat-ai/voice-ui-kit/styles.css";
import {
  usePipecatClientMicControl,
  usePipecatClientTransportState,
} from "@pipecat-ai/client-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PersonaSelector } from "./components/PersonaSelector";
import { ActivityPanel } from "./components/ActivityPanel";
import { OutputTree } from "./components/OutputTree";
import { FilePreview } from "./components/FilePreview";
import { VoiceInstrument } from "./components/VoiceInstrument";
import type { VoiceState } from "./components/VoiceInstrument";
import { useActivityLog } from "./hooks/useActivityLog";
import { useAudioLevel } from "./hooks/useAudioLevel";
import "./App.css";

function ThemeToggle() {
  const [, forceUpdate] = useState(0);

  const getTheme = () =>
    document.documentElement.getAttribute("data-theme") === "light"
      ? "light"
      : "dark";

  useEffect(() => {
    const stored = localStorage.getItem("voxcat-theme");
    if (stored === "light" || stored === "dark") {
      document.documentElement.setAttribute("data-theme", stored);
    }
  }, []);

  const toggle = () => {
    const next = getTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("voxcat-theme", next);
    forceUpdate((n) => n + 1);
  };

  const theme = getTheme();

  return (
    <button className="theme-toggle" onClick={toggle} title={theme === "dark" ? "Light mode" : "Dark mode"}>
      {theme === "dark" ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      )}
    </button>
  );
}

function useElapsed(running: boolean): string {
  const [seconds, setSeconds] = useState(0);
  const startRef = useRef(Date.now());

  useEffect(() => {
    if (!running) return;
    startRef.current = Date.now();
    setSeconds(0);
    const id = setInterval(() => {
      setSeconds(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [running]);

  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function deriveVoiceState(
  entries: ReturnType<typeof useActivityLog>["entries"],
  speaking: boolean,
  isMicEnabled: boolean,
  connecting: boolean,
): { state: VoiceState; toolName?: string } {
  if (connecting) return { state: "connecting" };
  if (!isMicEnabled) return { state: "muted" };

  const lastToolStart = [...entries]
    .reverse()
    .find((e) => e.kind === "tool-start");
  const lastToolResult = [...entries]
    .reverse()
    .find((e) => e.kind === "tool-result");

  if (
    lastToolStart &&
    (!lastToolResult || lastToolResult.timestamp < lastToolStart.timestamp)
  ) {
    return {
      state: "working",
      toolName:
        lastToolStart.kind === "tool-start"
          ? lastToolStart.functionName
          : undefined,
    };
  }

  if (speaking) return { state: "speaking" };
  return { state: "listening" };
}

function SessionView({
  handleDisconnect,
  persona,
  outputDir,
}: {
  handleDisconnect?: () => void;
  persona: string;
  outputDir: string;
}) {
  const { entries, speaking } = useActivityLog();
  const { enableMic, isMicEnabled } = usePipecatClientMicControl();
  const [muted, setMuted] = useState(false);
  const [unmuting, setUnmuting] = useState(false);

  useEffect(() => {
    if (unmuting && isMicEnabled) {
      setMuted(false);
      setUnmuting(false);
    }
  }, [unmuting, isMicEnabled]);
  const transportState = usePipecatClientTransportState();
  const connected =
    transportState === "ready" || transportState === "connected";
  const connecting =
    transportState === "connecting" ||
    transportState === "authenticating" ||
    transportState === "initializing";
  const [ended, setEnded] = useState(false);
  const [selected, setSelected] = useState<{
    persona: string;
    filename: string;
  } | null>(null);

  const { state: voiceState, toolName } = deriveVoiceState(
    entries,
    speaking,
    !muted,
    connecting,
  );
  const elapsed = useElapsed(connected || ended ? true : false);
  const currentVoiceState: VoiceState = ended ? "ended" : voiceState;
  const micActive =
    currentVoiceState === "listening" || currentVoiceState === "speaking";
  const audioLevels = useAudioLevel(micActive);

  return (
    <div className="session">
      {/* Rail */}
      <div className="rail">
        <div className="rail-left">
          <div className="rail-inline">
            <span className="wordmark">VOXCAT</span>
            <span className="rail-dot-sep">·</span>
            <span className="rail-persona-label">{persona}</span>
            <span className="rail-dot-sep">·</span>
            <span className="rail-output-dir">{outputDir}</span>
          </div>
        </div>
        <div className="rail-centre">
          <VoiceInstrument
            state={currentVoiceState}
            elapsed={elapsed}
            toolName={toolName}
            outputDir={outputDir}
            levels={audioLevels}
          />
        </div>
        <div className="rail-right">
          <ThemeToggle />
          {ended ? (
            <button
              className="btn-rail"
              onClick={() => window.location.reload()}
            >
              NEW SESSION
            </button>
          ) : (
            <>
              <div className="mic-indicator">
                <div
                  className={`mic-dot ${unmuting ? "mic-dot-syncing" : ""}`}
                  style={muted && !unmuting ? { background: "var(--text-5)" } : {}}
                />
                <span className="mic-label">
                  {unmuting ? "SYNCING" : muted ? "MIC OFF" : "MIC ON"}
                </span>
              </div>
              <button
                className="btn-rail"
                disabled={unmuting}
                onClick={() => {
                  if (muted) {
                    setUnmuting(true);
                    enableMic(true);
                  } else {
                    setMuted(true);
                    enableMic(false);
                  }
                }}
              >
                {unmuting ? "SYNCING" : muted ? "UNMUTE" : "MUTE"}
              </button>
              <button
                className="btn-rail end"
                onClick={() => {
                  handleDisconnect?.();
                  setEnded(true);
                }}
              >
                END
              </button>
            </>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="body-grid">
        <Group orientation="horizontal" id="session-panels">
          <Panel defaultSize={38} minSize={20} id="timeline">
            <ActivityPanel
          entries={entries}
          speaking={speaking}
          onFileClick={(filename) =>
            setSelected({ persona, filename })
          }
        />
          </Panel>
          <Separator className="grid-separator" />
          <Panel defaultSize={22} minSize={12} id="output">
            <OutputTree
              persona={persona}
              selected={selected}
              onSelect={(p, f) => setSelected({ persona: p, filename: f })}
            />
          </Panel>
          <Separator className="grid-separator" />
          <Panel defaultSize={40} minSize={20} id="document">
            <FilePreview selected={selected} />
          </Panel>
        </Group>
      </div>
    </div>
  );
}

function SessionPage({
  persona,
  outputDir,
  context,
  sessionFile,
}: {
  persona: string;
  outputDir: string;
  context?: string;
  sessionFile?: string;
}) {
  return (
    <PipecatAppBase
      transportType="smallwebrtc"
      startBotParams={{
        endpoint: "/start",
        requestData: {
          transport: "webrtc",
          enableDefaultIceServers: true,
          body: {
            persona,
            ...(context ? { context } : {}),
            ...(sessionFile ? { session_file: sessionFile } : {}),
          },
        },
      }}
      connectOnMount
    >
      {(props: PipecatBaseChildProps) => (
        <SessionView
          handleDisconnect={props.handleDisconnect}
          persona={persona}
          outputDir={outputDir}
        />
      )}
    </PipecatAppBase>
  );
}

function PastSessions({
  onContinue,
  onBack,
}: {
  onContinue: (persona: string, context: string, sessionFile: string) => void;
  onBack: () => void;
}) {
  const [sessions, setSessions] = useState<
    Array<{ persona: string; filename: string; modified: number }>
  >([]);
  const [selected, setSelected] = useState<{
    persona: string;
    filename: string;
  } | null>(null);
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch("/api/sessions")
      .then((r) => r.json())
      .then((d) => setSessions(d.sessions || []));
  }, []);

  useEffect(() => {
    if (!selected) return;
    fetch(`/api/sessions/${selected.persona}/${selected.filename}`)
      .then((r) => r.json())
      .then((d) => setContent(d.content || ""));
  }, [selected?.persona, selected?.filename]);

  return (
    <div className="app">
      <div className="landing-header">
        <div className="wordmark">VOXCAT</div>
        <div className="landing-header-right">
          <span
            className="landing-header-link"
            onClick={onBack}
          >
            NEW SESSION
          </span>
          <ThemeToggle />
        </div>
      </div>
      <div className="landing-body">
        <div className="landing-left" style={{ gap: 0, padding: 0 }}>
          <div className="pane" style={{ height: "100%" }}>
            <div className="pane-header" style={{ padding: "13px 24px" }}>
              <span className="pane-label">PAST SESSIONS</span>
              <span className="pane-meta">{sessions.length} SESSIONS</span>
            </div>
            <div className="vx-scroll" style={{ flex: 1, overflowY: "auto" }}>
              {sessions.map((s) => (
                <div
                  key={`${s.persona}/${s.filename}`}
                  className={`output-file ${
                    selected?.persona === s.persona &&
                    selected?.filename === s.filename
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    setSelected({ persona: s.persona, filename: s.filename })
                  }
                  style={{ paddingLeft: 24 }}
                >
                  <span style={{ color: "var(--text-4)", marginRight: 8 }}>
                    {s.persona.toUpperCase()}
                  </span>
                  {s.filename}
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="landing-right" style={{ padding: "0", gap: 0 }}>
          {selected ? (
            <div className="pane" style={{ height: "100%" }}>
              <div className="pane-header pane-header-document">
                <span
                  className="doc-header-name pane-meta-interactive"
                  title="Click to rename"
                  onClick={() => {
                    const name = prompt("Rename session:", selected.filename.replace(".md", ""));
                    if (!name) return;
                    fetch(`/api/sessions/${selected.persona}/${selected.filename}/rename?new_name=${encodeURIComponent(name)}`, { method: "POST" })
                      .then((r) => r.json())
                      .then((d) => {
                        if (d.filename) {
                          setSelected({ persona: selected.persona, filename: d.filename });
                          fetch("/api/sessions").then((r) => r.json()).then((d) => setSessions(d.sessions || []));
                        }
                      });
                  }}
                >
                  {selected.filename}
                </span>
                <button
                  className="btn-primary"
                  style={{ padding: "8px 16px", fontSize: "10px" }}
                  onClick={() => onContinue(selected.persona, content, selected.filename)}
                >
                  CONTINUE SESSION
                </button>
              </div>
              <div className="doc-scroll vx-scroll">
                <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
              </div>
            </div>
          ) : (
            <div className="doc-empty">Select a session to preview</div>
          )}
        </div>
      </div>
    </div>
  );
}

function LandingPage({
  onStart,
  onContinue,
}: {
  onStart: (persona: string) => void;
  onContinue: (persona: string, context: string, sessionFile: string) => void;
}) {
  const [persona, setPersona] = useState("thinking-partner");
  const [view, setView] = useState<"select" | "history">("select");

  if (view === "history") {
    return (
      <PastSessions
        onContinue={onContinue}
        onBack={() => setView("select")}
      />
    );
  }

  return (
    <div className="app">
      <div className="landing-header">
        <div className="wordmark">VOXCAT</div>
        <div className="landing-header-right">
          <span>GEMINI LIVE · SMALLWEBRTC</span>
          <span
            className="landing-header-link"
            onClick={() => setView("history")}
          >
            PAST SESSIONS
          </span>
          <ThemeToggle />
        </div>
      </div>
      <div className="landing-body">
        <div className="landing-left">
          <div>
            <div className="landing-hero">
              Think out loud.
              <br />
              Keep the notes.
            </div>
            <div className="landing-desc">
              A voice session with a role you choose. Every answer, search and
              file written lands in that role's own folder.
            </div>
          </div>
          <div className="landing-specs">
            <div className="landing-spec-row">
              <span className="landing-spec-label">LATENCY</span>
              <span className="landing-spec-value">
                ~300 ms speech to speech
              </span>
            </div>
            <div className="landing-spec-row">
              <span className="landing-spec-label">TOOLS</span>
              <span className="landing-spec-value">
                websearch · file read / write · MCP, read-only
              </span>
            </div>
            <div className="landing-spec-row">
              <span className="landing-spec-label">OUTPUT</span>
              <span className="landing-spec-value">markdown, on your disk or NotebookLM</span>
            </div>
          </div>
        </div>
        <div className="landing-right">
          <div className="landing-section-label">SELECT PERSONA</div>
          <PersonaSelector value={persona} onChange={setPersona} />
          <div className="landing-footer">
            <button className="btn-primary" onClick={() => onStart(persona)}>
              START SESSION
            </button>
            <span className="landing-mic-note">MICROPHONE REQUIRED</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState<{
    persona: string;
    outputDir: string;
    context?: string;
    sessionFile?: string;
  } | null>(null);

  if (session) {
    return (
      <SessionPage
        persona={session.persona}
        outputDir={session.outputDir}
        context={session.context}
        sessionFile={session.sessionFile}
      />
    );
  }

  return (
    <LandingPage
      onStart={(p) =>
        setSession({ persona: p, outputDir: `output/${p}/` })
      }
      onContinue={(p, ctx, file) =>
        setSession({ persona: p, outputDir: `output/${p}/`, context: ctx, sessionFile: file })
      }
    />
  );
}
