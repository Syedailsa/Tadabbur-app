import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";

export default function WaveForm() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const initAudio = async () => {
      try {
        // Access Microphone
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioContext();
        audioContextRef.current = audioCtx;

        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256; 
        analyserRef.current = analyser;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        dataArrayRef.current = dataArray;

        const source = audioCtx.createMediaStreamSource(stream);
        sourceRef.current = source;
        source.connect(analyser);

        draw();
      } catch (err) {
        console.error("Error accessing microphone for visualizer:", err);
      }
    };

    const draw = () => {
      const canvas = canvasRef.current;
      const analyser = analyserRef.current;
      const dataArray = dataArrayRef.current;

      if (!canvas || !analyser || !dataArray) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const width = canvas.width;
      const height = canvas.height;

      analyser.getByteFrequencyData(dataArray as any); 

      ctx.clearRect(0, 0, width, height);

      const barWidth = (width / dataArray.length) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < dataArray.length; i++) {
        barHeight = dataArray[i] / 2; 

        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, "#a855f7"); // Purple
        gradient.addColorStop(1, "#3b82f6"); // Blue

        ctx.fillStyle = gradient;

        const y = (height - barHeight) / 2;
        
        ctx.fillRect(x, y, barWidth, barHeight);

        x += barWidth + 2; // Spacing
      }

      animationFrameRef.current = requestAnimationFrame(draw);
    };

    initAudio();

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (streamRef.current) streamRef.current.getTracks().forEach(track => track.stop());
      if (audioContextRef.current) audioContextRef.current.close();
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className="w-full h-32 flex items-center justify-center bg-gray-50/90 backdrop-blur-sm rounded-lg border border-gray-200 shadow-inner p-4"
    >
        <div className="absolute top-2 left-4 text-xs font-semibold text-gray-500 animate-pulse">
            Listening...
        </div>
        <canvas
            ref={canvasRef}
            width={600}
            height={100}
            className="w-full h-full object-contain"
        />
    </motion.div>
  );
}