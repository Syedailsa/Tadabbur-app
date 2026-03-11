import React, { useContext, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { ChatContext } from "@/app/context/chatbot/ChatContext";

export default function WaveForm() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const { currentMode } = useContext(ChatContext)!

  useEffect(() => {
    const initAudio = async () => {
      try {
        // Access Microphone
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        // @ts-expect-error window type is uncertain
        const AudioContext = window.AudioContext || window.webkitAudioContext;
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

      //@ts-expect-error data array types don't match with arg
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, width, height);

      const barWidth = (width / dataArray.length) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < dataArray.length; i++) {
        barHeight = dataArray[i] / 3;

        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        // all black waveforms
        gradient.addColorStop(0, currentMode === "normal" ? "#000000" : "#ffffff");
        gradient.addColorStop(1, currentMode === "normal" ? "#000000" : "#ffffff");

        ctx.fillStyle = gradient;

        const y = (height - barHeight) / 2;

        const radius = barWidth; // adjust if you want less rounding

        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, radius);
        ctx.fill();

        x += barWidth + 3; // Spacing
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
      className="w-full flex items-center"
    >
      <div className={`ml-auto mt-auto w-50 ${currentMode === "normal" ? "bg-white shadow-md" : "bg-black shadow-sm shadow-red-500"} rounded-full px-4 py-3`}>
        <canvas
          ref={canvasRef}
          width={300}
          height={27}
          className="w-full h-full object-contain"
        />
      </div>
    </motion.div>
  );
}