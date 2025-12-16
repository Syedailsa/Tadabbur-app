"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Reciter {
  id: string;
  name: string;
}

interface AudioDialogProps {
  isOpen: boolean;
  onClose: () => void;
  parsedRequest: {
    surah: number;
    ayah?: number;
  };
  originalMessage: string;
  availableReciters: Reciter[];
  wsRef: React.MutableRefObject<WebSocket | null>;
}

export default function QuranAudioDialog({
  isOpen,
  onClose,
  parsedRequest,
  originalMessage,
  availableReciters,
  wsRef,
}: AudioDialogProps) {
  const [selectedReciter, setSelectedReciter] = useState<string>("alafasy");
  const [audioData, setAudioData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentAyahIndex, setCurrentAyahIndex] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (isOpen && wsRef.current) {
      // Listen for audio responses
      const handleMessage = (event: MessageEvent) => {
        const data = JSON.parse(event.data);

        if (data.type === "audio_response") {
          setLoading(false);
          if (data.status === "success") {
            setAudioData(data.data);
            setError(null);
          } else {
            setError(data.message || "Failed to fetch audio");
          }
        }
      };

      wsRef.current.addEventListener("message", handleMessage);

      return () => {
        wsRef.current?.removeEventListener("message", handleMessage);
      };
    }
  }, [isOpen, wsRef]);

  const handlePlay = () => {
    if (!wsRef.current) return;

    setLoading(true);
    setError(null);

    wsRef.current.send(
      JSON.stringify({
        type: "audio_request",
        surah: parsedRequest.surah,
        ayah: parsedRequest.ayah || null,
        reciter: selectedReciter,
      })
    );
  };

  const playAyah = (index: number) => {
    if (audioData?.ayahs && audioData.ayahs[index]) {
      const ayah = audioData.ayahs[index];
      if (audioRef.current) {
        audioRef.current.src = ayah.audio_url;
        audioRef.current.play();
        setCurrentAyahIndex(index);
      }
    }
  };

  const handleAudioEnd = () => {
    // Auto-play next ayah
    if (
      audioData?.ayahs &&
      currentAyahIndex < audioData.ayahs.length - 1
    ) {
      playAyah(currentAyahIndex + 1);
    }
  };

  useEffect(() => {
    if (audioData && audioRef.current) {
      if (audioData.type === "single_ayah") {
        audioRef.current.src = audioData.ayah.audio_url;
        audioRef.current.play();
      } else if (audioData.type === "complete_surah" && audioData.ayahs?.length > 0) {
        playAyah(0);
      }
    }
  }, [audioData]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40"
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 
                     bg-white rounded-xl shadow-2xl p-6 w-[90%] max-w-2xl z-50"
          >
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-800">
                🎵 Quran Audio Player
              </h2>
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ✕
              </button>
            </div>

            {/* Original Message */}
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-semibold">Your request:</span>{" "}
                {originalMessage}
              </p>
            </div>

            {/* Surah Info */}
            <div className="mb-4">
              <p className="text-lg">
                <span className="font-semibold">Surah:</span> {parsedRequest.surah}
                {parsedRequest.ayah && (
                  <>
                    {" "}
                    | <span className="font-semibold">Ayah:</span>{" "}
                    {parsedRequest.ayah}
                  </>
                )}
              </p>
            </div>

            {/* Reciter Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Reciter:
              </label>
              <select
                value={selectedReciter}
                onChange={(e) => setSelectedReciter(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 
                         focus:ring-green-500 focus:border-transparent"
              >
                {availableReciters.map((reciter) => (
                  <option key={reciter.id} value={reciter.id}>
                    {reciter.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
                <p className="text-red-600 text-sm">❌ {error}</p>
              </div>
            )}

            {/* Audio Player */}
            {audioData && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <h3 className="font-bold text-green-800 mb-2">
                  {audioData.surah.englishName} ({audioData.surah.name})
                </h3>

                {audioData.type === "single_ayah" && (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-700">
                      Ayah {audioData.ayah.number}
                    </p>
                    <p className="text-right text-xl leading-loose">
                      {audioData.ayah.text}
                    </p>
                  </div>
                )}

                {audioData.type === "complete_surah" && (
                  <div className="space-y-2">
                    <p className="text-sm text-gray-600">
                      Total Ayahs: {audioData.ayahs?.length || 0}
                    </p>
                    <p className="text-sm text-green-700">
                      Playing: Ayah {currentAyahIndex + 1}
                    </p>

                    {/* Ayah List */}
                    <div className="max-h-60 overflow-y-auto mt-3 space-y-2">
                      {audioData.ayahs?.map((ayah: any, index: number) => (
                        <button
                          key={index}
                          onClick={() => playAyah(index)}
                          className={`w-full text-left p-2 rounded-lg transition-colors ${
                            currentAyahIndex === index
                              ? "bg-green-100 border border-green-300"
                              : "bg-white border border-gray-200 hover:bg-gray-50"
                          }`}
                        >
                          <span className="font-semibold text-sm">
                            Ayah {ayah.number}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Hidden Audio Element */}
                <audio
                  ref={audioRef}
                  controls
                  onEnded={handleAudioEnd}
                  className="w-full mt-3"
                />
              </div>
            )}

            {/* Play Button */}
            {!audioData && (
              <button
                onClick={handlePlay}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold 
                         py-3 px-6 rounded-lg transition-colors disabled:opacity-50 
                         disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <span className="animate-spin">⏳</span>
                    Loading...
                  </>
                ) : (
                  <>
                    <span>▶️</span>
                    Play Audio
                  </>
                )}
              </button>
            )}

            {/* Reciter Info */}
            {audioData && (
              <div className="mt-4 text-center text-sm text-gray-500">
                Reciter: {audioData.reciter.name}
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}