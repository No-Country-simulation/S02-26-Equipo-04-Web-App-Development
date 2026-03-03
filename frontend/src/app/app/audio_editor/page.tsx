"use client";

import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserAudioItem, type UserClipItem, type UserVideoItem, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Music2 } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const MIN_AUDIO_SEGMENT_SECONDS = 5;

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

function isTerminalStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed" || normalized === "failed" || normalized === "error";
}

function isDoneStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed";
}

function toTimeLabel(seconds: number) {
  const min = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const sec = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${min}:${sec}`;
}

function clamp(value: number, min: number, max: number) {
  if (Number.isNaN(value)) {
    return min;
  }
  return Math.min(Math.max(value, min), max);
}

export default function AudioEditorPage() {
  const searchParams = useSearchParams();
  const preferredVideoId = searchParams.get("videoId")?.trim() ?? "";
  const preferredClipId = searchParams.get("clipId")?.trim() ?? "";
  const token = useAuthStore((state) => state.token);

  const [videos, setVideos] = useState<UserVideoItem[]>([]);
  const [isLoadingVideos, setIsLoadingVideos] = useState(true);
  const [videoError, setVideoError] = useState<string | null>(null);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [focusedClip, setFocusedClip] = useState<UserClipItem | null>(null);

  const [audios, setAudios] = useState<UserAudioItem[]>([]);
  const [isLoadingAudios, setIsLoadingAudios] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);
  const [selectedAudioId, setSelectedAudioId] = useState<string | null>(null);
  const [selectedAudioUrl, setSelectedAudioUrl] = useState<string | null>(null);

  const [audioOffsetSec, setAudioOffsetSec] = useState(0);
  const [audioStartSec, setAudioStartSec] = useState(0);
  const [audioEndSec, setAudioEndSec] = useState(15);
  const [audioVolume, setAudioVolume] = useState(1);
  const [videoDurationSec, setVideoDurationSec] = useState(0);
  const [audioDurationSec, setAudioDurationSec] = useState(0);

  const [isSubmittingAudio, setIsSubmittingAudio] = useState(false);
  const [audioSubmitInfo, setAudioSubmitInfo] = useState<string | null>(null);
  const [audioSubmitError, setAudioSubmitError] = useState<string | null>(null);
  const [audioJobId, setAudioJobId] = useState<string | null>(null);
  const [isPollingAudioJob, setIsPollingAudioJob] = useState(false);
  const [mixedVideoUrl, setMixedVideoUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoadingVideos(false);
      setVideoError("No encontramos una sesion activa para cargar videos.");
      return;
    }

    let cancelled = false;

    const loadVideos = async () => {
      setIsLoadingVideos(true);
      setVideoError(null);
      try {
        let selectedClip: UserClipItem | null = null;
        let preferredVideoFromQuery = preferredVideoId;

        if (preferredClipId) {
          try {
            const clipResponse = await videoApi.getMyClipById(preferredClipId, token);
            selectedClip = clipResponse.clip;
            if (selectedClip && !preferredVideoFromQuery) {
              preferredVideoFromQuery = selectedClip.video_id;
            }
          } catch {
            selectedClip = null;
          }
        }

        const targetVideoId = preferredVideoFromQuery || selectedClip?.video_id || "";
        if (!targetVideoId) {
          setVideos([]);
          setFocusedClip(null);
          setSelectedVideoId(null);
          setVideoError("Selecciona un video o clip desde Biblioteca para abrir el Audio editor.");
          return;
        }

        const targetVideo = await videoApi.getMyVideoById(targetVideoId, token);

        if (cancelled) {
          return;
        }

        setVideos([
          {
            video_id: targetVideo.video_id,
            filename: targetVideo.filename,
            status: targetVideo.status,
            uploaded_at: targetVideo.uploaded_at,
            preview_url: targetVideo.preview_url
          }
        ]);
        setFocusedClip(selectedClip);
        setSelectedVideoId(targetVideo.video_id);
      } catch (loadError) {
        if (!cancelled) {
          setVideoError(normalizeVideoError(loadError, "No pudimos cargar tus videos."));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingVideos(false);
        }
      }
    };

    void loadVideos();

    return () => {
      cancelled = true;
    };
  }, [token, preferredClipId, preferredVideoId]);

  useEffect(() => {
    if (!token) {
      setAudios([]);
      return;
    }

    let cancelled = false;

    const loadAudios = async () => {
      setIsLoadingAudios(true);
      setAudioError(null);
      try {
        const response = await videoApi.getMyAudios(token, { limit: 50, offset: 0 });
        if (cancelled) {
          return;
        }

        setAudios(response.audios);
        setSelectedAudioId((prev) => {
          if (prev && response.audios.some((audio) => audio.audio_id === prev)) {
            return prev;
          }
          return response.audios[0]?.audio_id ?? null;
        });
      } catch (loadError) {
        if (!cancelled) {
          setAudioError(normalizeVideoError(loadError, "No pudimos cargar tus audios."));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingAudios(false);
        }
      }
    };

    void loadAudios();

    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    if (!token || !selectedAudioId) {
      setSelectedAudioUrl(null);
      setAudioDurationSec(0);
      return;
    }

    let cancelled = false;
    setAudioDurationSec(0);

    const resolveAudioUrl = async () => {
      try {
        const response = await videoApi.getAudioUrl(selectedAudioId, token);
        if (!cancelled) {
          setSelectedAudioUrl(response.url);
        }
      } catch {
        if (!cancelled) {
          setSelectedAudioUrl(null);
          setAudioDurationSec(0);
        }
      }
    };

    void resolveAudioUrl();

    return () => {
      cancelled = true;
    };
  }, [selectedAudioId, token]);

  useEffect(() => {
    if (!token || !audioJobId) {
      setIsPollingAudioJob(false);
      return;
    }

    let cancelled = false;

    const syncAudioJob = async () => {
      try {
        const status = await videoApi.getJobStatus(audioJobId, token);
        if (cancelled) {
          return;
        }

        if (status.output_path) {
          setMixedVideoUrl(status.output_path);
        }

        if (isDoneStatus(status.status)) {
          setAudioSubmitInfo(`Mezcla de audio lista. Job ${audioJobId.slice(0, 8)} finalizado.`);
        }

        if (isTerminalStatus(status.status) && (status.output_path || !isDoneStatus(status.status))) {
          window.clearInterval(intervalId);
          setIsPollingAudioJob(false);

          if (!isDoneStatus(status.status)) {
            setAudioSubmitError(`La mezcla termino con estado ${status.status}.`);
          }
        }
      } catch {
        if (!cancelled) {
          setAudioSubmitError("No pudimos actualizar el estado del job de mezcla.");
        }
      }
    };

    setIsPollingAudioJob(true);
    const intervalId = window.setInterval(() => {
      void syncAudioJob();
    }, 4000);

    void syncAudioJob();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsPollingAudioJob(false);
    };
  }, [audioJobId, token]);

  const selectedVideo = useMemo(() => videos.find((video) => video.video_id === selectedVideoId) ?? null, [videos, selectedVideoId]);
  const previewUrl = mixedVideoUrl ?? focusedClip?.output_path ?? selectedVideo?.preview_url ?? null;

  useEffect(() => {
    if (!previewUrl) {
      setVideoDurationSec(0);
      return;
    }

    const video = document.createElement("video");
    const onLoaded = () => {
      setVideoDurationSec(Number.isFinite(video.duration) ? video.duration : 0);
    };
    const onError = () => {
      setVideoDurationSec(0);
    };

    video.preload = "metadata";
    video.src = previewUrl;
    video.addEventListener("loadedmetadata", onLoaded);
    video.addEventListener("error", onError);

    return () => {
      video.removeEventListener("loadedmetadata", onLoaded);
      video.removeEventListener("error", onError);
      video.src = "";
    };
  }, [previewUrl]);

  const maxOffsetSec = useMemo(() => {
    if (videoDurationSec <= 0) {
      return 0;
    }
    return Math.max(Math.floor(videoDurationSec) - MIN_AUDIO_SEGMENT_SECONDS, 0);
  }, [videoDurationSec]);

  const maxAudioStartSec = useMemo(() => {
    if (audioDurationSec <= 0) {
      return 0;
    }
    return Math.max(Math.floor(audioDurationSec) - MIN_AUDIO_SEGMENT_SECONDS, 0);
  }, [audioDurationSec]);

  const maxAudioEndSec = useMemo(() => {
    const byAudio = audioDurationSec > 0 ? Math.floor(audioDurationSec) : Number.POSITIVE_INFINITY;
    const byVideo = videoDurationSec > 0 ? Math.floor(videoDurationSec) : Number.POSITIVE_INFINITY;
    return Math.min(byAudio, byVideo);
  }, [audioDurationSec, videoDurationSec]);

  useEffect(() => {
    const nextOffset = clamp(audioOffsetSec, 0, maxOffsetSec);
    const nextStart = clamp(audioStartSec, 0, maxAudioStartSec);

    const availableByAudio = audioDurationSec > 0 ? Math.max(Math.floor(audioDurationSec) - nextStart, 0) : Number.POSITIVE_INFINITY;
    const availableByVideo = videoDurationSec > 0 ? Math.max(Math.floor(videoDurationSec) - nextOffset, 0) : Number.POSITIVE_INFINITY;
    const maxSegment = Math.max(Math.min(availableByAudio, availableByVideo), 0);
    const minEnd = nextStart + Math.min(MIN_AUDIO_SEGMENT_SECONDS, maxSegment);
    const maxEnd = nextStart + maxSegment;

    const nextEnd = clamp(audioEndSec, minEnd, maxEnd || minEnd);

    if (nextOffset !== audioOffsetSec) {
      setAudioOffsetSec(nextOffset);
    }
    if (nextStart !== audioStartSec) {
      setAudioStartSec(nextStart);
    }
    if (nextEnd !== audioEndSec) {
      setAudioEndSec(nextEnd);
    }
  }, [audioDurationSec, audioEndSec, audioOffsetSec, audioStartSec, maxAudioStartSec, maxOffsetSec, videoDurationSec]);

  const selectedSegmentDurationSec = Math.max(audioEndSec - audioStartSec, 0);
  const canSubmitAudioJob =
    Boolean(selectedVideoId) &&
    Boolean(selectedAudioId) &&
    selectedSegmentDurationSec >= MIN_AUDIO_SEGMENT_SECONDS &&
    (videoDurationSec <= 0 || audioOffsetSec + selectedSegmentDurationSec <= Math.floor(videoDurationSec));

  const audioOffsetPct = videoDurationSec > 0 ? Math.min((audioOffsetSec / videoDurationSec) * 100, 100) : 0;
  const audioWidthPct = videoDurationSec > 0 ? Math.min((selectedSegmentDurationSec / videoDurationSec) * 100, 100 - audioOffsetPct) : 0;

  const handleAddAudioToVideo = async () => {
    if (!token || !selectedVideoId || !selectedAudioId) {
      setAudioSubmitError("Selecciona video y audio para iniciar la mezcla.");
      return;
    }

    if (selectedSegmentDurationSec < MIN_AUDIO_SEGMENT_SECONDS) {
      setAudioSubmitError(`El segmento de audio debe durar al menos ${MIN_AUDIO_SEGMENT_SECONDS} segundos.`);
      return;
    }

    if (videoDurationSec > 0 && audioOffsetSec + selectedSegmentDurationSec > Math.floor(videoDurationSec)) {
      setAudioSubmitError("La pista de audio no puede exceder la duracion total del video.");
      return;
    }

    setIsSubmittingAudio(true);
    setAudioSubmitError(null);
    setAudioSubmitInfo(null);
    setMixedVideoUrl(null);

    try {
      const response = await videoApi.addAudioToVideo(selectedVideoId, token, {
        audio_id: selectedAudioId,
        audio_offset_sec: Math.max(0, Math.floor(audioOffsetSec)),
        audio_start_sec: Math.max(0, Math.floor(audioStartSec)),
        audio_end_sec: Math.max(MIN_AUDIO_SEGMENT_SECONDS, Math.ceil(audioEndSec)),
        audio_volume: Math.round(clamp(audioVolume, 1, 2))
      });

      setAudioJobId(response.job_id);
      setAudioSubmitInfo(`Mezcla enviada a cola. Job ${response.job_id.slice(0, 8)} en estado ${response.status}.`);
    } catch (mixError) {
      setAudioSubmitError(normalizeVideoError(mixError, "No pudimos enviar el job para mezclar audio."));
    } finally {
      setIsSubmittingAudio(false);
    }
  };

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">audio editor</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Video + pista de audio</h3>

          <div className="mt-3 rounded-xl border border-neon-violet/30 bg-neon-violet/10 px-3 py-2 text-xs text-neon-violet/90">
            Para cambiar de video, abrilo desde Biblioteca en la card de video o clip.
          </div>

          {isLoadingVideos ? (
            <p className="mt-4 text-sm text-white/70">Cargando videos...</p>
          ) : videoError ? (
            <p className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{videoError}</p>
          ) : previewUrl ? (
            <VideoPreview videoPreviewUrl={previewUrl} onTrimChange={() => {}} />
          ) : (
            <p className="mt-4 text-sm text-white/70">Selecciona un video con preview disponible.</p>
          )}

          <div className="mt-4 rounded-xl border border-neon-violet/30 bg-neon-violet/5 p-3">
            <p className="text-xs uppercase tracking-[0.16em] text-neon-violet/85">Pistas</p>
            <div className="mt-2 grid gap-2">
              <div className="rounded-lg border border-white/10 bg-night-900/80 p-2">
                <p className="text-[11px] text-white/65">Track video</p>
                <div className="mt-2 h-6 rounded bg-gradient-to-r from-sky-400/25 to-sky-300/60" />
              </div>
              <div className="rounded-lg border border-white/10 bg-night-900/80 p-2">
                <div className="flex items-center justify-between text-[11px] text-white/65">
                  <span>Track audio</span>
                  <span>
                    {toTimeLabel(audioStartSec)} - {toTimeLabel(audioEndSec)}
                  </span>
                </div>
                <div className="mt-2 h-6 overflow-hidden rounded bg-night-950/90">
                  <div
                    className="h-full rounded bg-gradient-to-r from-neon-violet/65 to-neon-magenta/75"
                    style={{
                      marginLeft: `${audioOffsetPct}%`,
                      width: `${Math.max(audioWidthPct, 2)}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {!isLoadingVideos && !selectedVideoId ? (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
              <p>No hay video seleccionado para este editor.</p>
              <Link
                href="/app/library"
                className="mt-3 inline-flex items-center justify-center rounded-lg border border-neon-violet/40 bg-neon-violet/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-neon-violet transition hover:bg-neon-violet/20"
              >
                Ir a Biblioteca
              </Link>
            </div>
          ) : null}
        </Panel>

        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">mezcla</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Ajustes de audio</h3>

          {isLoadingAudios ? <p className="mt-3 text-sm text-white/70">Cargando audios...</p> : null}
          {audioError ? <p className="mt-3 text-sm text-rose-200">{audioError}</p> : null}

          {!isLoadingAudios && audios.length > 0 ? (
            <>
              <label className="mt-3 block text-xs text-white/75">
                Audio de biblioteca
                <select
                  value={selectedAudioId ?? ""}
                  onChange={(event) => setSelectedAudioId(event.target.value || null)}
                  className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                >
                  {audios.map((audio) => (
                    <option key={audio.audio_id} value={audio.audio_id}>
                      {audio.filename}
                    </option>
                  ))}
                </select>
              </label>

              {selectedAudioUrl ? (
                <audio
                  controls
                  preload="metadata"
                  className="mt-3 w-full rounded-lg [accent-color:#cba6f7]"
                  src={selectedAudioUrl}
                  onLoadedMetadata={(event) => {
                    const duration = event.currentTarget.duration;
                    setAudioDurationSec(Number.isFinite(duration) ? duration : 0);
                  }}
                />
              ) : null}

              <p className="mt-2 text-[11px] text-white/65">
                Duracion de video: {videoDurationSec > 0 ? toTimeLabel(videoDurationSec) : "-"} · Duracion de audio: {audioDurationSec > 0 ? toTimeLabel(audioDurationSec) : "-"}
              </p>

              <div className="mt-3 rounded-xl border border-white/12 bg-white/5 p-3 text-xs text-white/80">
                <p className="text-neon-violet">Referencia rapida</p>
                <p className="mt-1">- `offset en video`: segundo del video donde empieza a sonar el audio.</p>
                <p>- `inicio audio`: desde que segundo del archivo de audio recortas.</p>
                <p>- `fin audio`: hasta que segundo del archivo de audio usas.</p>
                <p>- `volumen`: ganancia del audio agregado (1 = normal, 2 = fuerte).</p>
              </div>

              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <label className="text-xs text-white/75">
                  Offset en video (seg)
                  <input
                    type="number"
                    min={0}
                    max={maxOffsetSec}
                    value={audioOffsetSec}
                    onChange={(event) => setAudioOffsetSec(clamp(Number(event.target.value || 0), 0, maxOffsetSec))}
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
                 <label className="text-xs text-white/75">
                   Volumen (1 - 2)
                   <input
                     type="number"
                     min={1}
                     max={2}
                     step={1}
                     value={audioVolume}
                     onChange={(event) => setAudioVolume(clamp(Number(event.target.value || 1), 1, 2))}
                     className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                   />
                 </label>
                <label className="text-xs text-white/75">
                  Inicio audio (seg)
                  <input
                    type="number"
                    min={0}
                    max={maxAudioStartSec}
                    value={audioStartSec}
                    onChange={(event) => setAudioStartSec(clamp(Number(event.target.value || 0), 0, maxAudioStartSec))}
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
                <label className="text-xs text-white/75">
                  Fin audio (seg)
                  <input
                    type="number"
                    min={audioStartSec + MIN_AUDIO_SEGMENT_SECONDS}
                    max={Math.max(audioStartSec + MIN_AUDIO_SEGMENT_SECONDS, maxAudioEndSec)}
                    value={audioEndSec}
                    onChange={(event) =>
                      setAudioEndSec(
                        clamp(
                          Number(event.target.value || audioStartSec + MIN_AUDIO_SEGMENT_SECONDS),
                          audioStartSec + MIN_AUDIO_SEGMENT_SECONDS,
                          Math.max(audioStartSec + MIN_AUDIO_SEGMENT_SECONDS, maxAudioEndSec)
                        )
                      )
                    }
                    className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-violet/50"
                  />
                </label>
              </div>

              {!canSubmitAudioJob ? (
                <p className="mt-2 text-xs text-amber-200">
                  Ajusta la pista para que no exceda la duracion del video y tenga al menos {MIN_AUDIO_SEGMENT_SECONDS}s.
                </p>
              ) : null}

              <button
                type="button"
                onClick={() => void handleAddAudioToVideo()}
                disabled={!canSubmitAudioJob || isSubmittingAudio}
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-neon-violet/45 bg-neon-violet/15 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-neon-violet transition hover:bg-neon-violet/20 disabled:opacity-40"
              >
                <Music2 size={14} /> {isSubmittingAudio ? "Encolando..." : "Aplicar audio al video"}
              </button>

              {audioSubmitInfo ? <p className="mt-2 text-xs text-neon-mint">{audioSubmitInfo}</p> : null}
              {audioSubmitError ? <p className="mt-2 text-xs text-rose-200">{audioSubmitError}</p> : null}
              {isPollingAudioJob ? <p className="mt-2 text-xs text-white/65">Procesando mezcla de audio...</p> : null}
            </>
          ) : null}

          {!isLoadingAudios && audios.length === 0 ? (
            <p className="mt-3 text-sm text-white/70">No hay audios cargados. Subi uno desde Home para mezclarlo aca.</p>
          ) : null}
        </Panel>
      </div>
    </section>
  );
}
