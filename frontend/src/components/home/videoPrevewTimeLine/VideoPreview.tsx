"use client";
import { useEffect, useRef, useState } from "react";
import { VideoPlayer } from "./VideoPlayer";
import { Timeline } from "./Timeline";

type Props = {
  videoPreviewUrl: string | null;
  onTrimChange?: (start: number, end: number) => void;
};

export function VideoPreview({
  videoPreviewUrl,
  onTrimChange,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [duration, setDuration] = useState(0);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const loaded = () => {
        const duration = video.duration || 0;
      setDuration(duration);
       setStart(0);
      setEnd(duration);
    };

    video.addEventListener("loadedmetadata", loaded);
    return () => video.removeEventListener("loadedmetadata", loaded);
  }, [videoPreviewUrl]);

  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-sm">
        <span className="text-white/80">Preview</span>
      </div>

      <VideoPlayer start={start} end={end} duration={duration} videoRef={videoRef} src={videoPreviewUrl} />

      {duration > 0 && (
        <Timeline
          duration={duration}
          videoRef={videoRef}
           onTrimChange={(s, e) => {
            setStart(s);
            setEnd(e);
            onTrimChange?.(s, e);
          }}
        />
      )}
    </div>
  );
}
