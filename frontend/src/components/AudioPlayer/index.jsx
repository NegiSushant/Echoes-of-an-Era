import { useRef, useState, useEffect } from 'react';
import { Play, Pause } from 'lucide-react';
import { api } from '../../services/api';

export default function AudioPlayer({ audioId, initialTime = 0, autoPlay = false, title = "Grandfather's Voice" }) {
  const audioRef = useRef(null);
  const hasAppliedInitialTime = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const streamUrl = audioId ? api.getAudioStreamUrl(audioId) : null;
  const startSec = Math.max(0, parseFloat(initialTime) || 0);

  // Reset initial seek tracking whenever a new audio or start timestamp is passed
  useEffect(() => {
    hasAppliedInitialTime.current = false;
  }, [audioId, initialTime]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch((err) => {
        console.warn("Playback error:", err);
      });
    }
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (!audioRef.current) return;
    const dur = audioRef.current.duration;
    const validDur = isNaN(dur) ? 0 : dur;
    setDuration(validDur);

    // Apply the start timestamp only once per track
    if (!hasAppliedInitialTime.current) {
      hasAppliedInitialTime.current = true;
      if (startSec > 0) {
        // If starting timestamp is within duration, jump to it; otherwise start from beginning
        const targetSec = (validDur > 0 && startSec < validDur) ? startSec : 0;
        try {
          audioRef.current.currentTime = targetSec;
          setCurrentTime(targetSec);
        } catch (e) {
          console.warn("Could not seek to initial time:", e);
        }
      } else {
        audioRef.current.currentTime = 0;
        setCurrentTime(0);
      }
    }

    if (autoPlay) {
      audioRef.current.play().then(() => setIsPlaying(true)).catch((err) => {
        console.warn("Autoplay deferred or blocked by browser:", err);
        setIsPlaying(false);
      });
    }
  };


  const handleSeek = (e) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const skipSeconds = (delta) => {
    if (audioRef.current) {
      const nextTime = Math.max(0, Math.min(duration, audioRef.current.currentTime + delta));
      audioRef.current.currentTime = nextTime;
      setCurrentTime(nextTime);
    }
  };

  const formatTime = (secs) => {
    if (!secs || isNaN(secs)) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  if (!audioId) {
    return (
      <div className="glass-panel p-4 rounded-xl text-center text-xs text-slate-500 border border-slate-800">
        Select a memory or quotation to hear grandfather's authentic voice.
      </div>
    );
  }

  return (
    <div className="glass-panel p-4 rounded-2xl border border-amber-600/40 bg-slate-950/95 shadow-2xl backdrop-blur-xl">
      <audio
        ref={audioRef}
        src={streamUrl}
        preload="metadata"
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={() => setIsPlaying(false)}
        onError={(e) => {
          console.error("Audio playback error:", e);
          setIsPlaying(false);
        }}
      />

      {/* Header Info */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center space-x-2 truncate mr-3">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse flex-shrink-0" />
          <div className="truncate">
            <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-bold block">
              Authentic Voice Archive &bull; {startSec > 0 ? `Jumped to ${formatTime(startSec)}` : 'Full Story'}
            </span>
            <span className="text-xs font-semibold text-white truncate block">
              {title}
            </span>
          </div>
        </div>

        <span className="text-xs font-mono text-amber-300/90 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 flex-shrink-0">
          {formatTime(currentTime)} / {formatTime(duration)}
        </span>
      </div>

      {/* Controls & Scrubber */}
      <div className="flex items-center space-x-3">
        <button
          onClick={() => skipSeconds(-5)}
          className="p-1.5 text-slate-400 hover:text-amber-300 rounded-lg hover:bg-slate-800 transition text-xs font-mono"
          title="Rewind 5s"
        >
          -5s
        </button>

        <button
          onClick={togglePlay}
          className="p-3 bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold rounded-full transition shadow-lg shadow-amber-500/20 cursor-pointer flex-shrink-0"
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 ml-0.5 fill-current" />}
        </button>

        <button
          onClick={() => skipSeconds(5)}
          className="p-1.5 text-slate-400 hover:text-amber-300 rounded-lg hover:bg-slate-800 transition text-xs font-mono"
          title="Fast forward 5s"
        >
          +5s
        </button>

        <div className="flex-1">
          <input
            type="range"
            min="0"
            max={duration || 100}
            step="0.1"
            value={currentTime}
            onChange={handleSeek}
            className="w-full accent-amber-500 h-2 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}
