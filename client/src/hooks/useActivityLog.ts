import { useCallback, useRef, useState } from "react";
import { RTVIEvent } from "@pipecat-ai/client-js";
import { useRTVIClientEvent } from "@pipecat-ai/client-react";
import type { ActivityEntry } from "../types";

export function useActivityLog() {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [speaking, setSpeaking] = useState(false);
  const add = useCallback(
    (entry: ActivityEntry) => setEntries((prev) => [...prev, entry]),
    [],
  );

  const botIndex = useRef(-1);

  useRTVIClientEvent(RTVIEvent.UserTranscript, (data: any) => {
    if (data.final) {
      add({ kind: "user", text: data.text, timestamp: Date.now() });
      botIndex.current = -1;
    }
  });

  const appendBotText = useCallback((text: string) => {
    setEntries((prev) => {
      if (botIndex.current >= 0 && botIndex.current < prev.length) {
        const updated = [...prev];
        const existing = updated[botIndex.current];
        if (existing.kind === "bot") {
          updated[botIndex.current] = {
            ...existing,
            text: existing.text + text,
          };
          return updated;
        }
      }
      botIndex.current = prev.length;
      return [...prev, { kind: "bot", text, timestamp: Date.now() }];
    });
  }, []);

  useRTVIClientEvent(RTVIEvent.BotLlmText, (data: any) => {
    appendBotText(data.text);
  });

  useRTVIClientEvent(RTVIEvent.BotTtsText, (data: any) => {
    setSpeaking(true);
  });

  useRTVIClientEvent(RTVIEvent.BotStoppedSpeaking, () => {
    botIndex.current = -1;
    setSpeaking(false);
  });

  useRTVIClientEvent(RTVIEvent.LLMFunctionCallStarted, (data: any) => {
    botIndex.current = -1;
    add({
      kind: "tool-start",
      functionName: data.function_name,
      toolCallId: data.tool_call_id || "",
      timestamp: Date.now(),
    });
  });

  useRTVIClientEvent(RTVIEvent.LLMFunctionCallStopped, (data: any) => {
    add({
      kind: "tool-result",
      functionName: data.function_name,
      toolCallId: data.tool_call_id || "",
      result: data.result,
      cancelled: data.cancelled || false,
      timestamp: Date.now(),
    });
  });

  const clear = useCallback(() => {
    setEntries([]);
    botIndex.current = -1;
  }, []);

  return { entries, speaking, clear, add };
}
