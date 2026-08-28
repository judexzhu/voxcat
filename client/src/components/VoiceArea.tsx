import { VoiceVisualizer, ConnectButton } from "@pipecat-ai/voice-ui-kit";
import { usePipecatClientMicControl } from "@pipecat-ai/client-react";

export function VoiceArea() {
  const { enableMic, isMicEnabled } = usePipecatClientMicControl();

  return (
    <div className="voice-area">
      <VoiceVisualizer participantType="bot" />
      <div className="voice-controls">
        <ConnectButton />
        <button
          className="mute-btn"
          onClick={() => enableMic(!isMicEnabled)}
          title={isMicEnabled ? "Mute" : "Unmute"}
        >
          {isMicEnabled ? "🎤" : "🔇"}
        </button>
      </div>
    </div>
  );
}
