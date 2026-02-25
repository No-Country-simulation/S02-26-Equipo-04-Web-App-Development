"use client";
import { useEffect, useRef, useState } from "react";

type DragType = "start" | "end" | null;
const MIN_CLIP_SECONDS = 5;

export function useVideoTrim(
  duration: number,
  videoRef: React.RefObject<HTMLVideoElement | null>,
  containerWidth: number,
  onTrimChange?: (start: number, end: number) => void
) {
  const [startPx, setStartPx] = useState(0);
  const [endPx, setEndPx] = useState(containerWidth);
  const [playheadPx, setPlayheadPx] = useState(0);

  const dragging = useRef<DragType>(null);

  const pixelsPerSecond =
    duration > 0 && containerWidth > 0
      ? containerWidth / duration
      : 1;
  const minGapPx = Math.max(MIN_CLIP_SECONDS * pixelsPerSecond, 1);

  // init
  useEffect(() => {
    setEndPx(containerWidth);
  }, [containerWidth]);

  // sync playhead
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const update = () => {
      setPlayheadPx(video.currentTime * pixelsPerSecond);
    };

    video.addEventListener("timeupdate", update);
    return () => video.removeEventListener("timeupdate", update);
  }, [pixelsPerSecond, videoRef]);

  function notify(start: number, end: number) {
    onTrimChange?.(start, end);
  }

  function startDrag(type: DragType) {
    dragging.current = type;

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", stopDrag);
  }

  function stopDrag() {
    dragging.current = null;
    window.removeEventListener("mousemove", onMouseMove);
    window.removeEventListener("mouseup", stopDrag);
  }

  function onMouseMove(e: MouseEvent) {
    if (!dragging.current) return;

    const rect = (
      e.target as HTMLElement
    ).closest("[data-timeline]")?.getBoundingClientRect();

    if (!rect) return;

    const x = e.clientX - rect.left;

    if (dragging.current === "start") {
      const newStart = Math.min(Math.max(0, x), endPx - minGapPx);
      setStartPx(newStart);
      notify(newStart / pixelsPerSecond, endPx / pixelsPerSecond);
    }

    if (dragging.current === "end") {
      const newEnd = Math.max(Math.min(containerWidth, x), startPx + minGapPx);
      setEndPx(newEnd);
      notify(startPx / pixelsPerSecond, newEnd / pixelsPerSecond);
    }
  }

  function seek(e: React.MouseEvent) {
    if (!videoRef.current) return;

    const rect = (
      e.target as HTMLElement
    ).closest("[data-timeline]")?.getBoundingClientRect();

    if (!rect) return;

    const x = e.clientX - rect.left;
    videoRef.current.currentTime = x / pixelsPerSecond;
  }

  return {
    startPx,
    endPx,
    playheadPx,
    pixelsPerSecond,
    startDrag,
    seek,
  };
}
