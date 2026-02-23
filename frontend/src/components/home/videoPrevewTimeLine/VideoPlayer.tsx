"use client";
import { useEffect, useState } from "react";
import { ControlPlayer } from "../../ui/ControlPlayer";

type Props = {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  src: string | null;
  start?: number;
  end?: number;
  duration?:number;
};

export function VideoPlayer({
  videoRef,
  duration,
  src,
  start = 0,
  end,
}: Props) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [timeNow, setTimeNow] = useState(0);
  const [volume, setVolume] = useState(1);
  const volumenFunction = (event:React.ChangeEvent<HTMLInputElement>)=>{
    const value = Number(event.target.value)
    setVolume(value);
    if(videoRef.current){
      videoRef.current.volume = value;
    }
  }
  // =========================
  // Limitar reproducción al trim
  // =========================
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    function handleTimeUpdate() {
        if (!video) return;
        
        setTimeNow(Math.round(video.currentTime))
      if (end !== undefined && video.currentTime >= end) {
        video.pause();
        video.currentTime = start;
        
        setIsPlaying(false);
      }

    }
   
    video.addEventListener("timeupdate", handleTimeUpdate);

    return () =>
      video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [start, end, videoRef]);

  // =========================
  // Play / Pause
  // =========================
  function togglePlay() {
    const video = videoRef.current;
    if (!video) return;

    if (video.paused) {
      // arrancar desde el inicio del trim
      if (video.currentTime < start || video.currentTime > (end ?? Infinity)) {
        video.currentTime = start;
      }

      video.play();
      setIsPlaying(true);
    } else {
      video.pause();
      setIsPlaying(false);
    }
  }


  return (
    <div className=" relative mt-2 overflow-hidden rounded-lg border border-white/15 bg-black/40">
      
      {/* Video */}
      <video
        ref={videoRef}
        preload="metadata"
        className="w-full max-h-[400px] object-contain"
        src={src ?? undefined}
      />
      <ControlPlayer isPlaying={isPlaying} togglePlay={togglePlay} volume={volume} timeNow={timeNow} volumenFunction={volumenFunction} duration={duration} />

    </div>
  );
}
