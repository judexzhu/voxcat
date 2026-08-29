import { useEffect, useRef, useState } from "react";

const BAR_COUNT = 32;
const REST = Array(BAR_COUNT).fill(0.14);

export function useAudioLevel(active: boolean) {
  const [levels, setLevels] = useState<number[]>(REST);
  const ctxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef(0);
  const activeRef = useRef(active);
  const initRef = useRef(false);

  activeRef.current = active;

  useEffect(() => {
    if (!active) {
      setLevels(REST);
      cancelAnimationFrame(rafRef.current);
      return;
    }

    if (initRef.current && analyserRef.current) {
      startLoop();
      return;
    }

    let cancelled = false;

    async function init() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }

        const ctx = new AudioContext();
        ctxRef.current = ctx;

        const analyser = ctx.createAnalyser();
        analyser.fftSize = 64;
        analyser.smoothingTimeConstant = 0.7;
        analyserRef.current = analyser;

        const source = ctx.createMediaStreamSource(stream);
        source.connect(analyser);

        initRef.current = true;
        startLoop();
      } catch {
        // No mic access
      }
    }

    init();

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
    };
  }, [active]);

  function startLoop() {
    const analyser = analyserRef.current!;
    if (!analyser) return;
    const data = new Uint8Array(analyser.frequencyBinCount);

    function tick() {
      if (!activeRef.current) return;
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
  }

  return levels;
}
