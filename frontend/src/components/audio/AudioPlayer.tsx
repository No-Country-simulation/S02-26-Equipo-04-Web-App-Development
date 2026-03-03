"use client";

import { Pause, Play, Volume2, VolumeX } from "lucide-react";
import { type CSSProperties, useEffect, useMemo, useRef, useState } from "react";
import styles from "./AudioPlayer.module.css";

type AudioPlayerProps = {
  src: string;
  className?: string;
  onDurationChange?: (durationSec: number) => void;
};

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    return "0:00";
  }

  const totalSeconds = Math.floor(seconds);
  const min = Math.floor(totalSeconds / 60);
  const sec = totalSeconds % 60;
  return `${min}:${sec.toString().padStart(2, "0")}`;
}

export function AudioPlayer({ src, className, onDurationChange }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    const handleLoadedMetadata = () => {
      const nextDuration = Number.isFinite(audio.duration) ? audio.duration : 0;
      setDuration(nextDuration);
      onDurationChange?.(nextDuration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
    };

    const handleError = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      setDuration(0);
      onDurationChange?.(0);
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);
    audio.addEventListener("error", handleError);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
      audio.removeEventListener("error", handleError);
    };
  }, [onDurationChange]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    audio.volume = volume;
    audio.muted = isMuted;
  }, [isMuted, volume]);

  const progressPct = useMemo(() => {
    if (duration <= 0) {
      return 0;
    }
    return Math.min((currentTime / duration) * 100, 100);
  }, [currentTime, duration]);

  const waveformBars = useMemo(
    () => Array.from({ length: 30 }, (_, index) => 20 + ((index * 11 + 7) % 70)),
    []
  );

  const progressStyle = {
    "--progress": `${progressPct}%`
  } as CSSProperties;

  const volumeStyle = {
    "--progress": `${(isMuted ? 0 : volume) * 100}%`
  } as CSSProperties;

  const togglePlay = async () => {
    const audio = audioRef.current;
    if (!audio) {
      return;
    }

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    try {
      await audio.play();
      setIsPlaying(true);
    } catch {
      setIsPlaying(false);
    }
  };

  const handleSeek = (value: number) => {
    const audio = audioRef.current;
    if (!audio || duration <= 0) {
      return;
    }

    const nextTime = (value / 100) * duration;
    audio.currentTime = nextTime;
    setCurrentTime(nextTime);
  };

  return (
    <div className={["rounded-2xl border border-white/12 bg-gradient-to-b from-night-900/85 to-night-900/70 p-3.5", className ?? ""].join(" ")}>
      <audio ref={audioRef} preload="metadata" src={src} />

      <div className="grid grid-cols-[auto_1fr] gap-3">
        <button
          type="button"
          onClick={() => void togglePlay()}
          className="inline-flex h-10 w-10 items-center justify-center self-center rounded-full border border-neon-violet/45 bg-neon-violet/15 text-neon-violet transition hover:bg-neon-violet/25"
          aria-label={isPlaying ? "Pausar audio" : "Reproducir audio"}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
        </button>

        <div className="min-w-0">
          <div className="mb-2 overflow-hidden rounded-xl border border-white/10 bg-night-950/80 px-2 py-1.5">
            <div className="flex h-6 items-end gap-1">
              {waveformBars.map((height, index) => {
                const active = progressPct >= ((index + 1) / waveformBars.length) * 100;
                return (
                  <span
                    key={`bar-${height}-${index}`}
                    className={[
                      "w-full rounded-full transition-colors duration-200",
                      active ? "bg-gradient-to-t from-neon-violet/70 to-neon-magenta/90" : "bg-white/15"
                    ].join(" ")}
                    style={{ height: `${height}%` }}
                  />
                );
              })}
            </div>
          </div>

          <div className="mb-1.5 flex items-center justify-between text-[11px] text-white/70">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="range"
              min={0}
              max={100}
              step={0.1}
              value={duration > 0 ? progressPct : 0}
              onChange={(event) => handleSeek(Number(event.target.value))}
              className={styles.slider}
              style={progressStyle}
              aria-label="Progreso de audio"
            />

            <button
              type="button"
              onClick={() => setIsMuted((prev) => !prev)}
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/20 bg-white/5 text-white/75 transition hover:border-neon-violet/40 hover:text-neon-violet"
              aria-label={isMuted ? "Activar audio" : "Silenciar audio"}
            >
              {isMuted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            </button>

            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={volume}
              onChange={(event) => setVolume(Number(event.target.value))}
              className={[styles.slider, styles.volume].join(" ")}
              style={volumeStyle}
              aria-label="Volumen"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
