export type VoiceState =
  | "connecting"
  | "listening"
  | "speaking"
  | "muted"
  | "working"
  | "ended";

interface Props {
  state: VoiceState;
  elapsed: string;
  toolName?: string;
  outputDir?: string;
  levels?: number[];
}

function Ring({ state }: { state: VoiceState }) {
  if (state === "connecting") {
    return (
      <div className="voice-ring">
        <div
          className="voice-ring-border"
          style={{
            border: "1px solid rgba(167,139,250,0.4)",
            animation: "vxHalo 1.6s ease-in-out infinite",
          }}
        />
        <div
          className="voice-ring-dot"
          style={{
            width: 9,
            height: 9,
            background: "rgba(139,92,246,0.6)",
          }}
        />
      </div>
    );
  }

  if (state === "listening") {
    return (
      <div className="voice-ring">
        <div
          className="voice-ring-border"
          style={{
            border: "1px solid rgba(167,139,250,0.45)",
            animation: "vxHalo 3s ease-in-out infinite",
          }}
        />
        <div
          className="voice-ring-dot"
          style={{
            width: 9,
            height: 9,
            background: "var(--accent)",
            boxShadow: "0 0 12px rgba(139,92,246,0.85)",
            animation: "vxBreathe 3s ease-in-out infinite",
          }}
        />
      </div>
    );
  }

  if (state === "speaking") {
    return (
      <div className="voice-ring">
        <div
          className="voice-ring-border"
          style={{
            background: "rgba(139,92,246,0.18)",
            animation: "vxHalo 1.9s ease-in-out infinite",
          }}
        />
        <div
          className="voice-ring-border"
          style={{ border: "1px solid rgba(167,139,250,0.6)" }}
        />
        <div
          className="voice-ring-dot"
          style={{
            width: 14,
            height: 14,
            background: "var(--accent)",
            boxShadow: "0 0 18px rgba(139,92,246,0.9)",
            animation: "vxBreathe 1.9s ease-in-out infinite",
          }}
        />
      </div>
    );
  }

  if (state === "muted") {
    return (
      <div className="voice-ring">
        <div
          className="voice-ring-border"
          style={{ border: "1px solid rgba(255,255,255,0.14)" }}
        />
        <div
          style={{
            width: 11,
            height: 1,
            background: "rgba(255,255,255,0.35)",
            transform: "rotate(-45deg)",
          }}
        />
      </div>
    );
  }

  if (state === "working") {
    return (
      <div className="voice-ring">
        <div
          className="voice-ring-border"
          style={{ border: "1px solid var(--rule)" }}
        />
        <div
          className="voice-ring-dot"
          style={{
            width: 9,
            height: 9,
            background: "var(--accent)",
            animation: "vxBreathe 1.1s ease-in-out infinite",
          }}
        />
      </div>
    );
  }

  // ended
  return (
    <div className="voice-ring">
      <div
        className="voice-ring-border"
        style={{ border: "1px solid rgba(255,255,255,0.12)" }}
      />
      <div
        style={{ width: 10, height: 1, background: "rgba(255,255,255,0.3)" }}
      />
    </div>
  );
}

function Meter({
  state,
  toolName,
  levels,
}: {
  state: VoiceState;
  toolName?: string;
  levels?: number[];
}) {
  if (state === "connecting") {
    return (
      <div className="voice-meter-track" style={{ width: 180 }}>
        <div
          className="voice-meter-sweep"
          style={{ width: "22%", animation: "vxSweep 1.4s linear infinite" }}
        />
      </div>
    );
  }

  if (state === "working") {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 180 }}>
        <div className="tool-dot" />
        <span className="tool-name">{toolName?.toUpperCase() || "TOOL"}</span>
        <div className="voice-meter-track" style={{ flex: 1 }}>
          <div
            className="voice-meter-sweep"
            style={{ width: "30%", animation: "vxSweep 1.2s linear infinite" }}
          />
        </div>
      </div>
    );
  }

  if (state === "ended") return null;

  const barCount = 32;
  const height = state === "speaking" ? 30 : 24;
  const frozen = state === "muted";
  const color = frozen ? "rgba(255,255,255,0.14)" : "var(--accent)";
  const hasRealLevels = levels && levels.length === barCount;

  return (
    <div className="voice-meter" style={{ gap: 3, height }}>
      {Array.from({ length: barCount }, (_, i) => (
        <div
          key={i}
          className="voice-meter-bar"
          style={{
            height: "100%",
            background: color,
            transform: `scaleY(${
              frozen ? 0.14 : hasRealLevels ? levels[i] : 0.14
            })`,
            transition: hasRealLevels ? "transform 0.05s linear" : undefined,
          }}
        />
      ))}
    </div>
  );
}

const STATE_LABELS: Record<VoiceState, string> = {
  connecting: "CONNECTING",
  listening: "LISTENING",
  speaking: "SPEAKING",
  muted: "MUTED",
  working: "WORKING",
  ended: "SESSION ENDED",
};

const SUB_LABELS: Record<VoiceState, string> = {
  connecting: "NEGOTIATING WEBRTC",
  listening: "",
  speaking: "",
  muted: "MIC OFF · SESSION LIVE",
  working: "TOOL CALL IN FLIGHT",
  ended: "",
};

export function VoiceInstrument({ state, elapsed, toolName, outputDir, levels }: Props) {
  const sub = SUB_LABELS[state];
  const elapsedLine =
    state === "listening" || state === "speaking"
      ? `${elapsed} ELAPSED`
      : state === "ended"
        ? `${elapsed} · TRANSCRIPT SAVED TO ${outputDir || ""}`
        : sub;

  return (
    <>
      <Ring state={state} />
      <Meter state={state} toolName={toolName} levels={levels} />
      <div className="voice-status">
        <div className="voice-state-label" style={
          state === "muted" || state === "ended"
            ? { color: "rgba(255,255,255,0.55)" }
            : undefined
        }>
          {STATE_LABELS[state]}
        </div>
        <div className="voice-elapsed">{elapsedLine}</div>
      </div>
    </>
  );
}
