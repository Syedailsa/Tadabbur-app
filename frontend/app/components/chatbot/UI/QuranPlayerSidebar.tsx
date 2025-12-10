'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, X } from 'lucide-react';

const RECITERS = {
  alafasy: { id: 'ar.alafasy', name: 'Mishary Al-Afasy' },
  abdulbasit: { id: 'ar.abdulbasitmurattal', name: 'Abdul Basit' },
  sudais: { id: 'ar.abdurrahmaansudais', name: 'Abdur-Rahman As-Sudais' },
  husary: { id: 'ar.husary', name: 'Mahmoud Khalil Al-Husary' },
  minshawi: { id: 'ar.minshawi', name: 'Mohamed Siddiq Al-Minshawi' }
};

interface QuranAudioPlayerProps {
  wsRef: React.MutableRefObject<WebSocket | null>;
}

export default function QuranAudioPlayer({ wsRef }: QuranAudioPlayerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedReciter, setSelectedReciter] = useState('alafasy');
  const [surahNumber, setSurahNumber] = useState(1);
  const [ayahNumber, setAyahNumber] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentAyah, setCurrentAyah] = useState<any>(null);
  const [error, setError] = useState('');
  const [playFullSurah, setPlayFullSurah] = useState(false);
  const [surahAyahs, setSurahAyahs] = useState<any[]>([]);
  const [currentAyahIndex, setCurrentAyahIndex] = useState(0);
  
  const audioRef = useRef<HTMLAudioElement>(null);

  // WebSocket listener
  useEffect(() => {
    if (!wsRef.current) return;

    const handler = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'audio_response') {
          setLoading(false);
          if (data.status === 'success') {
            const audioData = data.data;

            if (audioData.type === 'single_ayah') {
              setCurrentAyah({
                audio: audioData.audio_url,
                text: audioData.text,
                surahName: audioData.surah.englishName,
                surahNameArabic: audioData.surah.name,
                ayahInSurah: audioData.ayah_number,
                surahNumber: audioData.surah.number
              });
              if (audioRef.current) {
                audioRef.current.src = audioData.audio_url;
                audioRef.current.play();
                setIsPlaying(true);
              }
            } else if (audioData.type === 'complete_surah') {
              setSurahAyahs(audioData.ayahs);
              setCurrentAyahIndex(0);
              if (audioData.ayahs.length > 0) {
                const first = audioData.ayahs[0];
                setCurrentAyah({
                  audio: first.audio,
                  text: first.text,
                  surahName: audioData.surah.englishName,
                  surahNameArabic: audioData.surah.name,
                  ayahInSurah: first.number,
                  surahNumber: audioData.surah.number
                });
                if (audioRef.current) {
                  audioRef.current.src = first.audio;
                  audioRef.current.play();
                  setIsPlaying(true);
                }
              }
            }
          } else {
            setError(data.message || 'Audio load nahi hua');
          }
        }
      } catch (e) {
        // Ignore non-audio messages
      }
    };

    wsRef.current.addEventListener('message', handler);
    return () => wsRef.current?.removeEventListener('message', handler);
  }, [wsRef]);

  const loadAudio = () => {
    if (!wsRef.current) return alert("WebSocket connect nahi hai");

    setLoading(true);
    setError('');
    setCurrentAyah(null);

    const request = playFullSurah 
      ? `play surah ${surahNumber}`
      : `play surah ${surahNumber} ayah ${ayahNumber}`;

    wsRef.current.send(JSON.stringify({
      type: 'audio_request',
      request: request,
      reciter: selectedReciter
    }));
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      audioRef.current.paused ? audioRef.current.play() : audioRef.current.pause();
      setIsPlaying(!audioRef.current.paused);
    }
  };

  const nextAyah = () => {
    if (playFullSurah && currentAyahIndex < surahAyahs.length - 1) {
      setCurrentAyahIndex(i => i + 1);
      const next = surahAyahs[currentAyahIndex + 1];
      setCurrentAyah(prev => ({ ...prev, audio: next.audio, text: next.text, ayahInSurah: next.number }));
      audioRef.current!.src = next.audio;
      audioRef.current!.play();
    } else {
      setAyahNumber(n => n + 1);
      loadAudio();
    }
  };

  const prevAyah = () => {
    if (playFullSurah && currentAyahIndex > 0) {
      setCurrentAyahIndex(i => i - 1);
      const prev = surahAyahs[currentAyahIndex - 1];
      setCurrentAyah(current => ({ ...current, audio: prev.audio, text: prev.text, ayahInSurah: prev.number }));
      audioRef.current!.src = prev.audio;
      audioRef.current!.play();
    } else if (!playFullSurah && ayahNumber > 1) {
      setAyahNumber(n => n - 1);
      loadAudio();
    }
  };

  // Quran page image
  const getPageImage = () => {
    if (!currentAyah) return "";
    const page = Math.ceil((currentAyah.surahNumber - 1) * 604 / 114 + currentAyah.ayahInSurah / 15);
    return `https://everyayah.com/data/images_png/${page}.png`;
  };

  return (
    <>
      {/* Listen Quran Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-24 right-6 bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-4 rounded-full shadow-2xl flex items-center gap-3 text-lg font-bold z-40 hover:scale-105 transition"
      >
        Listen Quran
      </button>

      {/* Sidebar */}
      {isOpen && (
        <>
          <div className="fixed inset-0 bg-black/60 z-40" onClick={() => setIsOpen(false)} />
          <div className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-50 flex flex-col">
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-6 flex justify-between items-center">
              <h2 className="text-2xl font-bold">Quran Player</h2>
              <button onClick={() => setIsOpen(false)} className="p-2 hover:bg-white/20 rounded-full">
                <X size={28} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Quran Page Image */}
              {currentAyah && (
                <div className="bg-gray-100 rounded-2xl overflow-hidden shadow-xl">
                  <img src={getPageImage()} alt="Quran Page" className="w-full" />
                </div>
              )}

              {/* Controls */}
              <div className="space-y-4">
                <div>
                  <label className="block font-semibold mb-2">Reciter</label>
                  <select 
                    value={selectedReciter}
                    onChange={(e) => setSelectedReciter(e.target.value)}
                    className="w-full p-3 border rounded-lg"
                  >
                    {Object.entries(RECITERS).map(([key, r]) => (
                      <option key={key} value={key}>{r.name}</option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-3">
                  <input type="checkbox" checked={playFullSurah} onChange={(e) => setPlayFullSurah(e.target.checked)} />
                  <span>Play Full Surah</span>
                </label>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-semibold mb-2">Surah</label>
                    <input type="number" min="1" max="114" value={surahNumber} onChange={(e) => setSurahNumber(+e.target.value)} className="w-full p-3 border rounded-lg text-center" />
                  </div>
                  {!playFullSurah && (
                    <div>
                      <label className="block font-semibold mb-2">Ayah</label>
                      <input type="number" min="1" value={ayahNumber} onChange={(e) => setAyahNumber(+e.target.value)} className="w-full p-3 border rounded-lg text-center" />
                    </div>
                  )}
                </div>

                <button onClick={loadAudio} disabled={loading} className="w-full bg-green-600 text-white py-4 rounded-lg font-bold">
                  {loading ? "Loading..." : "Play"}
                </button>

                {error && <p className="text-red-600 text-center">{error}</p>}
              </div>

              {/* Player */}
              {currentAyah && (
                <div className="bg-gray-50 rounded-2xl p-6 text-center">
                  <h3 className="text-xl font-bold text-green-700">{currentAyah.surahName}</h3>
                  <p className="text-3xl my-4 leading-relaxed text-right" dir="rtl" style={{fontFamily: 'Amiri, serif'}}>
                    {currentAyah.text}
                  </p>
                  <p>Ayah {currentAyah.ayahInSurah}</p>

                  <div className="flex justify-center gap-6 mt-6">
                    <button onClick={prevAyah}><SkipBack size={32} /></button>
                    <button onClick={togglePlayPause} className="p-4 bg-green-600 rounded-full text-white">
                      {isPlaying ? <Pause size={40} /> : <Play size={40} />}
                    </button>
                    <button onClick={nextAyah}><SkipForward size={32} /></button>
                  </div>
                </div>
              )}
            </div>

            <audio ref={audioRef} onEnded={nextAyah} />
          </div>
        </>
      )}
    </>
  );
}