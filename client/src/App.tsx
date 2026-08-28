import { useState } from "react";
import { PipecatAppBase, VoiceVisualizer } from "@pipecat-ai/voice-ui-kit";
import type { PipecatBaseChildProps } from "@pipecat-ai/voice-ui-kit";
import "@pipecat-ai/voice-ui-kit/styles.css";
import {
  usePipecatClientMicControl,
  usePipecatClientTransportState,
} from "@pipecat-ai/client-react";
import { Group, Panel, Separator } from "react-resizable-panels";
import { PersonaSelector } from "./components/PersonaSelector";
import { ActivityPanel } from "./components/ActivityPanel";
import { FileExplorer } from "./components/FileExplorer";
import { useActivityLog } from "./hooks/useActivityLog";
import "./App.css";

function ConnectedView({
  handleDisconnect,
  persona,
}: {
  handleDisconnect?: () => void;
  persona: string;
}) {
  const { entries } = useActivityLog();
  const { enableMic, isMicEnabled } = usePipecatClientMicControl();

  return (
    <>
      <div className="topbar-connected">
        <div className="mini-orb" />
        <span className="listening-label">Listening</span>
        <div className="separator" />
        <button
          className="ctrl-btn"
          onClick={() => enableMic(!isMicEnabled)}
          title={isMicEnabled ? "Mute" : "Unmute"}
        >
          {isMicEnabled ? "🎤" : "🔇"}
        </button>
        <button className="ctrl-btn end" onClick={handleDisconnect} title="End">
          ✕
        </button>
      </div>
      <div className="main">
        <Group orientation="horizontal" id="voxcat-panels">
          <Panel defaultSize={40} minSize={20} id="activity">
            <div className="activity-pane">
              <ActivityPanel entries={entries} />
            </div>
          </Panel>
          <Separator className="resize-handle" />
          <Panel defaultSize={60} minSize={20} id="files">
            <FileExplorer persona={persona} />
          </Panel>
        </Group>
      </div>
    </>
  );
}

function AppInner({
  handleConnect,
  handleDisconnect,
  error,
  persona,
}: PipecatBaseChildProps & { persona: string }) {
  const transportState = usePipecatClientTransportState();
  const connected = transportState === "ready" || transportState === "connected";
  const connecting =
    transportState === "connecting" ||
    transportState === "authenticating" ||
    transportState === "initializing";

  if (error) {
    return <div className="error-msg">{String(error)}</div>;
  }

  if (connected) {
    return (
      <ConnectedView handleDisconnect={handleDisconnect} persona={persona} />
    );
  }

  return (
    <div className="pre-connect">
      <div className="orb-large">
        <VoiceVisualizer participantType="bot" />
      </div>
      <button
        className="connect-btn"
        onClick={handleConnect}
        disabled={connecting}
      >
        {connecting ? "Connecting..." : "Start Conversation"}
      </button>
    </div>
  );
}

export default function App() {
  const [persona, setPersona] = useState("thinking-partner");

  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">Voxcat</div>
        <div className="separator" />
        <PersonaSelector value={persona} onChange={setPersona} />
        <div className="topbar-spacer" />
      </header>
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
        initDevicesOnMount
      >
        {(props: PipecatBaseChildProps) => (
          <AppInner {...props} persona={persona} />
        )}
      </PipecatAppBase>
    </div>
  );
}
