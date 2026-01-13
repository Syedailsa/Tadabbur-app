import React, { useState, useEffect, useRef } from 'react';
import { X, ChevronLeft, ChevronRight, Book, Loader2, Download, Share2, Copy, Check, Volume2, VolumeX, Settings } from 'lucide-react';

interface VerseData {
  success: boolean;
  surah: number;
  ayah: number;
  surah_name_en: string;
  surah_name_ar: string;
  total_ayahs: number;
  revelation_type: string;
  arabic_text: string;
  arabic_edition: string;
  translation_text: string;
  translation_edition: string;
  translator_name: string;
  number_in_quran: number;
  number_in_surah: number;
  juz: number;
  manzil: number;
  ruku: number;
  hizb_quarter: number;
  sajda: boolean;
  images?: {
    normal: string;
    high_resolution: string;
  };
  audio?: {
    url: string;
    reciter: string;
    reciter_name: string;
  };
  can_go_previous: boolean;
  can_go_next: boolean;
}

interface QuranVerseDialogProps {
  isOpen: boolean;
  onClose: () => void;
  parsedRequest: { surah: number; ayah: number };
  originalMessage?: string;
  wsRef: React.MutableRefObject<WebSocket | null>;
  note?: string;
}

export default function QuranVerseDialog({
  isOpen,
  onClose,
  parsedRequest,
  originalMessage,
  wsRef,
  note
}: QuranVerseDialogProps) {
<<<<<<< HEAD
  const [currentSurah, setCurrentSurah] = useState(parsedRequest.surah);
  const [currentAyah, setCurrentAyah] = useState(parsedRequest.ayah);
  const [verseData, setVerseData] = useState<VerseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputSurah, setInputSurah] = useState(parsedRequest.surah.toString());
  const [inputAyah, setInputAyah] = useState(parsedRequest.ayah.toString());
=======
  const [currentSurah, setCurrentSurah] = useState(parsedRequest?.surah ?? 1);
  const [currentAyah, setCurrentAyah] = useState(parsedRequest?.ayah ?? 1);
  const [verseData, setVerseData] = useState<VerseData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [inputSurah, setInputSurah] = useState(parsedRequest?.surah?.toString() ?? "1");
  const [inputAyah, setInputAyah] = useState(parsedRequest?.ayah?.toString() ?? "1");

  // const [currentSurah, setCurrentSurah] = useState(parsedRequest.surah);
  // const [currentAyah, setCurrentAyah] = useState(parsedRequest.ayah);
  // const [verseData, setVerseData] = useState<VerseData | null>(null);
  // const [loading, setLoading] = useState(false);
  // const [error, setError] = useState<string | null>(null);
  // const [inputSurah, setInputSurah] = useState(parsedRequest.surah.toString());
  // const [inputAyah, setInputAyah] = useState(parsedRequest.ayah.toString());
>>>>>>> 0a9fd875e9285f0bbd715f6ad16060e0c201aa0a
  const [copied, setCopied] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [includeAudio, setIncludeAudio] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
<<<<<<< HEAD
    if (isOpen) {
      setCurrentSurah(parsedRequest.surah);
      setCurrentAyah(parsedRequest.ayah);
      setInputSurah(parsedRequest.surah.toString());
      setInputAyah(parsedRequest.ayah.toString());
      fetchVerse(parsedRequest.surah, parsedRequest.ayah);
    } else {
      // Cleanup audio when dialog closes
=======
    if (isOpen && parsedRequest) {
      const safeSurah = parsedRequest.surah ?? 1;
      const safeAyah = parsedRequest.ayah ?? 1;

      setCurrentSurah(safeSurah);
      setCurrentAyah(safeAyah);
      setInputSurah(safeSurah.toString());
      setInputAyah(safeAyah.toString());
      
      fetchVerse(safeSurah, safeAyah);
    } else {
>>>>>>> 0a9fd875e9285f0bbd715f6ad16060e0c201aa0a
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setIsPlaying(false);
    }
  }, [isOpen, parsedRequest]);

  useEffect(() => {
    if (!wsRef.current) return;

    const handleMessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);

      if (data.type === "verse_response") {
        setLoading(false);
        if (data.status === "success") {
          setVerseData(data.data);
          setError(null);
          
          // Setup audio if available
          if (data.data.audio?.url && includeAudio) {
            audioRef.current = new Audio(data.data.audio.url);
            audioRef.current.addEventListener('ended', () => setIsPlaying(false));
          }
        } else {
          setError(data.message || "Failed to fetch verse");
        }
      }
    };

    wsRef.current.addEventListener('message', handleMessage);
    return () => {
      wsRef.current?.removeEventListener('message', handleMessage);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [wsRef, includeAudio]);

  const fetchVerse = (surah: number, ayah: number) => {
    if (!wsRef.current) return;

    setLoading(true);
    setError(null);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlaying(false);

    wsRef.current.send(
      JSON.stringify({
        type: "verse_request",
        surah: surah,
        ayah: ayah,
        include_audio: includeAudio
      })
    );
  };

  const goToPrevious = () => {
    if (verseData?.can_go_previous) {
      const newAyah = currentAyah - 1;
      setCurrentAyah(newAyah);
      setInputAyah(newAyah.toString());
      fetchVerse(currentSurah, newAyah);
    }
  };

  const goToNext = () => {
    if (verseData?.can_go_next) {
      const newAyah = currentAyah + 1;
      setCurrentAyah(newAyah);
      setInputAyah(newAyah.toString());
      fetchVerse(currentSurah, newAyah);
    }
  };

  const handleManualChange = () => {
    const surah = parseInt(inputSurah);
    const ayah = parseInt(inputAyah);

    if (isNaN(surah) || isNaN(ayah) || surah < 1 || surah > 114 || ayah < 1) {
      setError("Invalid surah or ayah number");
      return;
    }

    setCurrentSurah(surah);
    setCurrentAyah(ayah);
    fetchVerse(surah, ayah);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleManualChange();
    } else if (e.key === 'ArrowLeft') {
      goToPrevious();
    } else if (e.key === 'ArrowRight') {
      goToNext();
    }
  };

  const copyToClipboard = () => {
    if (!verseData) return;

    let text = `${verseData.arabic_text}\n\n${verseData.translation_text}\n\n— Surah ${verseData.surah_name_en} (${verseData.surah}:${verseData.ayah})`;

    if (verseData.images) {
      text += `\n\nImage: ${verseData.images.normal}`;
    }

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareVerse = async () => {
    if (!verseData) return;

    let text = `${verseData.arabic_text}\n\n${verseData.translation_text}\n\n— Surah ${verseData.surah_name_en} (${verseData.surah}:${verseData.ayah})`;

    if (verseData.images) {
      text += `\n\nImage: ${verseData.images.normal}`;
    }

    if (navigator.share) {
      try {
        await navigator.share({ text, title: `Quran ${verseData.surah}:${verseData.ayah}` });
      } catch (err) {
        console.log('Share cancelled');
      }
    } else {
      copyToClipboard();
    }
  };

  const toggleAudio = () => {
    if (!audioRef.current || !verseData?.audio) return;
    
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[95vh] overflow-hidden flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 text-white p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white/20 backdrop-blur-sm rounded-xl p-3">
                <Book className="w-8 h-8" />
              </div>
              <div>
                <h2 className="text-2xl font-bold tracking-tight">Quran Verse Reader</h2>
                {verseData && (
                  <div className="flex items-center gap-3 mt-1">
                    <p className="text-emerald-100 text-sm">
                      {verseData.surah_name_en} ({verseData.surah_name_ar})
                    </p>
                    <span className="text-emerald-200">•</span>
                    <p className="text-emerald-100 text-sm">
                      Juz {verseData.juz} • {verseData.revelation_type}
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="hover:bg-white/20 rounded-lg p-2 transition-colors"
                title="Settings"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={onClose}
                className="hover:bg-white/20 rounded-lg p-2 transition-colors"
                title="Close"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-gray-50 border-b border-gray-200 p-4">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeAudio}
                  onChange={(e) => {
                    setIncludeAudio(e.target.checked);
                    if (verseData) {
                      fetchVerse(currentSurah, currentAyah);
                    }
                  }}
                  className="w-4 h-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span className="text-sm font-medium text-gray-700">Enable Audio Recitation</span>
              </label>
            </div>
          </div>
        )}

        {/* Navigation Controls */}
        <div className="bg-gray-50 p-4 border-b border-gray-200">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <button
              onClick={goToPrevious}
              disabled={!verseData?.can_go_previous || loading}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:shadow-sm"
            >
              <ChevronLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Previous</span>
            </button>

            <div className="flex items-center gap-3 flex-1 justify-center">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-600 font-semibold">Surah</label>
                <input
                  type="number"
                  min="1"
                  max="114"
                  value={inputSurah}
                  onChange={(e) => setInputSurah(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-center font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              <span className="text-3xl text-gray-400 mt-6 font-light">:</span>

              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-600 font-semibold">Ayah</label>
                <input
                  type="number"
                  min="1"
                  value={inputAyah}
                  onChange={(e) => setInputAyah(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-center font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleManualChange}
                disabled={loading}
                className="px-5 py-2 mt-6 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors font-medium shadow-sm hover:shadow-md"
              >
                Go
              </button>
            </div>

            <button
              onClick={goToNext}
              disabled={!verseData?.can_go_next || loading}
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-all hover:shadow-sm"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          {note && (
            <div className="mt-3 text-sm text-amber-800 bg-amber-50 border border-amber-200 px-4 py-2 rounded-lg">
              💡 {note}
            </div>
          )}
        </div>

        {/* Verse Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 gap-4">
              <Loader2 className="w-12 h-12 animate-spin text-emerald-600" />
              <p className="text-gray-600 font-medium">Loading verse...</p>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <X className="w-8 h-8 text-red-600" />
                </div>
                <p className="text-red-600 font-semibold text-lg mb-2">Error Loading Verse</p>
                <p className="text-gray-600 text-sm">{error}</p>
                <button
                  onClick={() => fetchVerse(currentSurah, currentAyah)}
                  className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          ) : verseData ? (
            <div className="space-y-6 max-w-3xl mx-auto">
              {/* Arabic Text */}
              <div className="relative">
                <div className="absolute -inset-4 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl opacity-50"></div>
                <div className="relative bg-white/80 backdrop-blur-sm rounded-xl p-8 shadow-sm border border-emerald-100">
                  <p 
                    className="text-4xl md:text-5xl leading-loose md:leading-loose font-arabic text-gray-900 text-right"
                    dir="rtl"
                    lang="ar"
                  >
                    {verseData.arabic_text}
                  </p>
                  {verseData.sajda && (
                    <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium">
                      🕌 Sajdah Verse
                    </div>
                  )}
                </div>
              </div>

              {/* Verse Image */}
              {verseData.images && (
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-xl p-4 border border-indigo-200">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-bold text-indigo-700 uppercase tracking-wider">
                      Verse Image
                    </h3>
                    <a
                      href={verseData.images.high_resolution}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-indigo-600 hover:text-indigo-800 underline"
                    >
                      View High Resolution
                    </a>
                  </div>
                  <div className="flex justify-center">
                    <img
                      src={verseData.images.normal}
                      alt={`Quran ${verseData.surah}:${verseData.ayah}`}
                      className="max-w-full h-auto rounded-lg shadow-md border border-gray-200"
                      loading="lazy"
                    />
                  </div>
                </div>
              )}

              {/* Audio Player */}
              {verseData.audio && (
                <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={toggleAudio}
                        className="p-3 bg-purple-600 hover:bg-purple-700 text-white rounded-full transition-colors shadow-md hover:shadow-lg"
                      >
                        {isPlaying ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                      </button>
                      <div>
                        <p className="font-semibold text-purple-900">Audio Recitation</p>
                        <p className="text-sm text-purple-700">{verseData.audio.reciter_name}</p>
                      </div>
                    </div>
                    {isPlaying && (
                      <div className="flex gap-1">
                        {[...Array(5)].map((_, i) => (
                          <div
                            key={i}
                            className="w-1 bg-purple-600 rounded-full animate-pulse"
                            style={{
                              height: `${Math.random() * 20 + 10}px`,
                              animationDelay: `${i * 0.1}s`
                            }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Translation */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-emerald-700 uppercase tracking-wider">
                    Translation
                  </h3>
                  <span className="text-xs text-gray-500 font-medium">{verseData.translator_name}</span>
                </div>
                <div className="bg-gray-50 rounded-xl p-6 border border-gray-200">
                  <p className="text-lg leading-relaxed text-gray-800">
                    {verseData.translation_text}
                  </p>
                </div>
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-3 border border-blue-200">
                  <p className="text-xs text-blue-700 font-semibold mb-1">In Quran</p>
                  <p className="text-lg font-bold text-blue-900">{verseData.number_in_quran}</p>
                </div>
                <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-lg p-3 border border-emerald-200">
                  <p className="text-xs text-emerald-700 font-semibold mb-1">In Surah</p>
                  <p className="text-lg font-bold text-emerald-900">{verseData.number_in_surah}/{verseData.total_ayahs}</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-3 border border-purple-200">
                  <p className="text-xs text-purple-700 font-semibold mb-1">Juz</p>
                  <p className="text-lg font-bold text-purple-900">{verseData.juz}</p>
                </div>
                <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-3 border border-amber-200">
                  <p className="text-xs text-amber-700 font-semibold mb-1">Ruku</p>
                  <p className="text-lg font-bold text-amber-900">{verseData.ruku}</p>
                </div>
              </div>

<<<<<<< HEAD
              {/* Action Buttons */}
=======
              {/* Action Buttons
>>>>>>> 0a9fd875e9285f0bbd715f6ad16060e0c201aa0a
              <div className="flex gap-3 pt-4">
                <button
                  onClick={copyToClipboard}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors font-medium text-gray-700"
                >
                  {copied ? <Check className="w-5 h-5 text-green-600" /> : <Copy className="w-5 h-5" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
                <button
                  onClick={shareVerse}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors font-medium shadow-sm hover:shadow-md"
                >
                  <Share2 className="w-5 h-5" />
                  Share
                </button>
<<<<<<< HEAD
              </div>
=======
              </div> */}
>>>>>>> 0a9fd875e9285f0bbd715f6ad16060e0c201aa0a
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
          <p className="text-xs text-gray-600 text-center">
            Use <kbd className="px-2 py-1 bg-gray-200 rounded text-xs font-mono">← →</kbd> arrow keys to navigate • <kbd className="px-2 py-1 bg-gray-200 rounded text-xs font-mono">Enter</kbd> to jump
          </p>
        </div>
      </div>
    </div>
  );
}