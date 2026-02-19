"use client";
import { Pause, Play, Volume2 } from "lucide-react";
import { useEffect, useState } from "react";

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
  const [handHover, setHandHover] = useState(false);
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
  const formatTime =(segundos:number) => {
    if(!segundos && segundos !== 0) return "0:00" 
    const totalSecond = Math.floor(segundos);
    const hora = Math.floor(segundos/3600);
    const minuto = Math.floor((segundos % 3600)/60) ;
    const seg = totalSecond % 60
    const padd = seg.toString().padStart(2, "0")
    if(hora > 0){
      const paddMin = minuto.toString().padStart(2, "0")
      return `${hora}:${paddMin}: ${padd}`
    }
    return `${minuto}:${padd}`
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

      {/* Controls */}
      <div className="absolute  bottom-2 left-2 overflow-hidden rounded-lg border border-white/15 bg-black/40">
        {isPlaying?(<Pause size={25}
        onClick={togglePlay}/>): <Play size={25} onClick={togglePlay}/>}
        
      </div>
           
      <div onMouseEnter={() =>setHandHover(true)} onMouseLeave={() => setHandHover(false)} className=" absolute bottom-2 right-2 rounded-full flex items-center gap-2 bg-black/30 px-2 py-1 overflow-hidden">
        <Volume2 className={`
      transition-transform duration-200 ${handHover ? "-translate-x-1":"translate-x-0"}`}/>
        {handHover && (<input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={volume}
          onChange={volumenFunction}
          className={`
          transition-all duration-300 ease-out
          ${handHover ? "w-24 opacity-100" : "w-0 opacity-0"}
        `}
        />)}
        <div >
          <span>{ formatTime(timeNow) }/ {formatTime(duration || 0)}</span>
        </div>  
      </div>
    </div>
  );
}
