// "use client";

// import { useState, useRef, useEffect } from "react";
// import { motion, AnimatePresence } from "framer-motion";
// import { Play, Pause, X, Volume2 } from "lucide-react";

// interface SimpleAudioDialogProps {
//   isOpen: boolean;
//   onClose: () => void;
//   audioData: {
//     surah: string;
//     ayah_number: string | null;
//     audio_url: string;
//     all_urls: string[];
//     text_response: string;
//   };
// }

// export default function SimpleAudioDialog({
//   isOpen,
//   onClose,
//   audioData,
// }: SimpleAudioDialogProps) {
//   const [isPlaying, setIsPlaying] = useState(false);
//   const [currentTime, setCurrentTime] = useState(0);
//   const [duration, setDuration] = useState(0);
//   const audioRef = useRef<HTMLAudioElement | null>(null);

//   useEffect(() => {
//     if (isOpen && audioRef.current && audioData.audio_url) {
//       audioRef.current.load();
//     }
//   }, [isOpen, audioData.audio_url]);

//   const togglePlayPause = () => {
//     if (audioRef.current) {
//       if (isPlaying) {
//         audioRef.current.pause();
//       } else {
//         audioRef.current.play();
//       }
//       setIsPlaying(!isPlaying);
//     }
//   };

//   const handleTimeUpdate = () => {
//     if (audioRef.current) {
//       setCurrentTime(audioRef.current.currentTime);
//     }
//   };

//   const handleLoadedMetadata = () => {
//     if (audioRef.current) {
//       setDuration(audioRef.current.duration);
//     }
//   };

//   const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const seekTime = (Number(e.target.value) / 100) * duration;
//     if (audioRef.current) {
//       audioRef.current.currentTime = seekTime;
//       setCurrentTime(seekTime);
//     }
//   };

//   const formatTime = (seconds: number) => {
//     if (isNaN(seconds)) return "0:00";
//     const mins = Math.floor(seconds / 60);
//     const secs = Math.floor(seconds % 60);
//     return `${mins}:${secs.toString().padStart(2, "0")}`;
//   };

//   if (!isOpen || !audioData) return null;

//   return (
//     <AnimatePresence>
//       {isOpen && (
//         <>
//           {/* Backdrop */}
//           <motion.div
//             initial={{ opacity: 0 }}
//             animate={{ opacity: 1 }}
//             exit={{ opacity: 0 }}
//             onClick={onClose}
//             className="fixed inset-0 bg-black/50 z-40 flex items-center justify-center p-4"
//           />

//           {/* Dialog */}
//           <motion.div
//             initial={{ opacity: 0, scale: 0.9 }}
//             animate={{ opacity: 1, scale: 1 }}
//             exit={{ opacity: 0, scale: 0.9 }}
//             className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2
//                        bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 z-50"
//           >
//             {/* Close Button */}
//             <button
//               onClick={onClose}
//               className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
//             >
//               <X size={24} />
//             </button>

//             {/* Header */}
//             <div className="text-center mb-6">
//               <div className="w-20 h-20 bg-gradient-to-br from-emerald-400 to-teal-600 rounded-full mx-auto mb-4 flex items-center justify-center">
//                 <Volume2 size={40} className="text-white" />
//               </div>
//               <h2 className="text-2xl font-bold text-gray-800">
//                 {audioData.surah}
//               </h2>
//               {audioData.ayah_number && (
//                 <p className="text-gray-600 mt-1">Ayah {audioData.ayah_number}</p>
//               )}
//             </div>

//             {/* Audio Player */}
//             <audio
//               ref={audioRef}
//               src={audioData.audio_url}
//               onTimeUpdate={handleTimeUpdate}
//               onLoadedMetadata={handleLoadedMetadata}
//               onEnded={() => setIsPlaying(false)}
//             />

//             {/* Progress Bar */}
//             <div className="mb-4">
//               <input
//                 type="range"
//                 min="0"
//                 max="100"
//                 value={(currentTime / duration) * 100 || 0}
//                 onChange={handleSeek}
//                 className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
//               />
//               <div className="flex justify-between text-sm text-gray-500 mt-2">
//                 <span>{formatTime(currentTime)}</span>
//                 <span>{formatTime(duration)}</span>
//               </div>
//             </div>

//             {/* Play/Pause Button */}
//             <button
//               onClick={togglePlayPause}
//               className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 text-white py-4 rounded-xl font-semibold text-lg hover:from-emerald-600 hover:to-teal-700 transition-all duration-200 flex items-center justify-center gap-3 shadow-lg"
//             >
//               {isPlaying ? (
//                 <>
//                   <Pause size={24} fill="white" />
//                   Pause
//                 </>
//               ) : (
//                 <>
//                   <Play size={24} fill="white" />
//                   Play Recitation
//                 </>
//               )}
//             </button>

//             {/* Additional Info */}
//             {audioData.all_urls && audioData.all_urls.length > 1 && (
//               <div className="mt-4 text-center text-sm text-gray-600">
//                 <p>{audioData.all_urls.length} ayahs available</p>
//               </div>
//             )}

//             {/* Reciter Info */}
//             <div className="mt-4 text-center text-xs text-gray-500">
//               Reciter: Mishary Rashid Alafasy
//             </div>
//           </motion.div>
//         </>
//       )}
//     </AnimatePresence>
//   );
// }


"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, X, Volume2, SkipForward, SkipBack } from "lucide-react";

interface SimpleAudioDialogProps {
  isOpen: boolean;
  onClose: () => void;
  audioData: {
    surah: string;
    ayah_number: string | null;
    audio_url: string;        
    all_urls: string[];      
    text_response?: string;
  };
}

export default function SimpleAudioDialog({
  isOpen,
  onClose,
  audioData,
}: SimpleAudioDialogProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentAyahIndex, setCurrentAyahIndex] = useState(0); 
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  
  const ayahCount = audioData.all_urls.length;
  const currentUrl = audioData.all_urls[currentAyahIndex] || audioData.audio_url;

  useEffect(() => {
    if (isOpen && audioRef.current) {
      audioRef.current.src = currentUrl;
      audioRef.current.load();
      
      audioRef.current.play().catch(() => {});
      setIsPlaying(true);
    }
  }, [isOpen, currentAyahIndex, currentUrl]);

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const nextAyah = () => {
    if (currentAyahIndex < ayahCount - 1) {
      setCurrentAyahIndex(currentAyahIndex + 1);
    } else {
      
      setIsPlaying(false);
    }
  };

  const prevAyah = () => {
    if (currentAyahIndex > 0) {
      setCurrentAyahIndex(currentAyahIndex - 1);
    }
  };

  const handleEnded = () => {
    nextAyah(); 
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
      setDuration(audioRef.current.duration || 0);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const seekTime = Number(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = seekTime;
      setCurrentTime(seekTime);
    }
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!isOpen || !audioData) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40 flex items-center justify-center p-4"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 z-50"
          >
            <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
              <X size={24} />
            </button>

            <div className="text-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-emerald-400 to-teal-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                <Volume2 size={40} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-800">{audioData.surah}</h2>
              <p className="text-gray-600 mt-1">
                آیت {currentAyahIndex + 1} / {ayahCount}
              </p>
            </div>

            <audio
              ref={audioRef}
              src={currentUrl}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleTimeUpdate}
              onEnded={handleEnded}
            />

            <div className="mb-4">
              <input
                type="range"
                min="0"
                max={duration || 0}
                value={currentTime}
                onChange={handleSeek}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-emerald-600"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-2">
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            <div className="flex justify-center gap-4 mb-4">
              <button onClick={prevAyah} disabled={currentAyahIndex === 0} className="p-3 rounded-full bg-gray-200 disabled:opacity-50">
                <SkipBack size={20} />
              </button>

              <button
                onClick={togglePlayPause}
                className="w-16 h-16 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-full font-semibold flex items-center justify-center shadow-lg"
              >
                {isPlaying ? <Pause size={32} /> : <Play size={32} />}
              </button>

              <button onClick={nextAyah} disabled={currentAyahIndex === ayahCount - 1} className="p-3 rounded-full bg-gray-200 disabled:opacity-50">
                <SkipForward size={20} />
              </button>
            </div>

            <div className="text-center text-xs text-gray-500">
              Reciter: Mishary Rashid Alafasy
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}