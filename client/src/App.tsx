import { useEffect, useRef, useState } from "react";
import { PipecatAppBase } from "@pipecat-ai/voice-ui-kit";
import type { PipecatBaseChildProps } from "@pipecat-ai/voice-ui-kit";
import "@pipecat-ai/voice-ui-kit/styles.css";
import {
  usePipecatClientMicControl,
  usePipecatClientTransportState,
} from "@pipecat-ai/client-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { PersonaSelector } from "./components/PersonaSelector";
import { ActivityPanel } from "./components/ActivityPanel";
import { OutputTree } from "./components/OutputTree";
import { FilePreview } from "./components/FilePreview";
import { VoiceInstrument } from "./components/VoiceInstrument";
import type { VoiceState } from "./components/VoiceInstrument";
import { useActivityLog } from "./hooks/useActivityLog";
import { useAudioLevel } from "./hooks/useAudioLevel";
import "./App.css";

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

function useVoiceState(
  entries: ReturnType<typeof useActivityLog>["entries"],
  speaking: boolean,
): {
  state: VoiceState;
  toolName?: string;
} {
  const transportState = usePipecatClientTransportState();
  const { isMicEnabled } = usePipecatClientMicControl();

  const connecting =
    transportState === "connecting" ||
    transportState === "authenticating" ||
    transportState === "initializing";

  if (connecting) return { state: "connecting" };

  if (!isMicEnabled) return { state: "muted" };

  // Check for in-flight tool call
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
  const transportState = usePipecatClientTransportState();
  const connected =
    transportState === "ready" || transportState === "connected";
  const [ended, setEnded] = useState(false);
  const [selected, setSelected] = useState<{
    persona: string;
    filename: string;
  } | null>(null);

  const { state: voiceState, toolName } = useVoiceState(entries, speaking);
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
                  className="mic-dot"
                  style={!isMicEnabled ? { background: "var(--text-5)" } : {}}
                />
                <span className="mic-label">
                  {isMicEnabled ? "MIC ON" : "MIC OFF"}
                </span>
              </div>
              <button
                className="btn-rail"
                onClick={() => enableMic(!isMicEnabled)}
              >
                {isMicEnabled ? "MUTE" : "UNMUTE"}
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
}: {
  persona: string;
  outputDir: string;
}) {
  return (
    <PipecatAppBase
      transportType="smallwebrtc"
      startBotParams={{
        endpoint: "/start",
        requestData: {
          transport: "webrtc",
          enableDefaultIceServers: true,
          body: { persona },
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

function LandingPage({ onStart }: { onStart: (persona: string) => void }) {
  const [persona, setPersona] = useState("thinking-partner");

  return (
    <div className="app">
      <div className="landing-header">
        <div className="wordmark">VOXCAT</div>
        <div className="landing-header-right">
          <span>GEMINI LIVE · SMALLWEBRTC</span>
          <span className="landing-header-link">PAST SESSIONS</span>
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
  } | null>(null);

  if (session) {
    return (
      <SessionPage persona={session.persona} outputDir={session.outputDir} />
    );
  }

  return (
    <LandingPage
      onStart={(p) =>
        setSession({
          persona: p,
          outputDir: `output/${p}/`,
        })
      }
    />
  );
}
