import { useEffect, useRef, useState } from "react";

const BAR_COUNT = 32;

export function useAudioLevel(active: boolean) {
  const [levels, setLevels] = useState<number[]>(() =>
    Array(BAR_COUNT).fill(0.14),
  );
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const rafRef = useRef(0);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!active) {
      setLevels(Array(BAR_COUNT).fill(0.14));
      return;
    }

    let cancelled = false;

    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;

        const ctx = new AudioContext();
        ctxRef.current = ctx;

        const analyser = ctx.createAnalyser();
        analyser.fftSize = 64;
        analyser.smoothingTimeConstant = 0.7;
        analyserRef.current = analyser;

        const source = ctx.createMediaStreamSource(stream);
        source.connect(analyser);
        sourceRef.current = source;

        const data = new Uint8Array(analyser.frequencyBinCount);

        function tick() {
          if (cancelled) return;
          analyser.getByteFrequencyData(data);

          const bars: number[] = [];
          const binCount = data.length;
          for (let i = 0; i < BAR_COUNT; i++) {
            const idx = Math.floor((i / BAR_COUNT) * binCount);
            const v = data[idx] / 255;
            bars.push(Math.max(0.14, v));
          }
          setLevels(bars);
          rafRef.current = requestAnimationFrame(tick);
        }

        rafRef.current = requestAnimationFrame(tick);
      } catch {
        // No mic access — stay at rest
      }
    }

    start();

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
      sourceRef.current?.disconnect();
      analyserRef.current?.disconnect();
      ctxRef.current?.close();
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      ctxRef.current = null;
      analyserRef.current = null;
      sourceRef.current = null;
    };
  }, [active]);

  return levels;
}
