"use client";

import { VideoSettings } from "@/src/components/home/VideoSettings";
import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserClipItem, type UserVideoItem, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useVideoSettingsStore } from "@/src/store/useVideoSettingsStore";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const MIN_CLIP_SECONDS = 5;
const TIMELINE_SESSION_KEY = "timeline:editor-session";

type StoredTimelineJob = {
  jobId: string;
  status: string | null;
  outputPath: string | null;
  updatedAt: string;
};

type TimelineSession = {
  lastVideoId: string | null;
  jobsByVideo: Record<string, StoredTimelineJob>;
};

const emptyTimelineSession: TimelineSession = {
  lastVideoId: null,
  jobsByVideo: {}
};

function normalizeJobStatus(status: string | null) {
  return (status ?? "PENDING").toLowerCase();
}

function isTerminalJobStatus(status: string | null) {
  const normalized = normalizeJobStatus(status);
  return normalized === "done" || normalized === "completed" || normalized === "failed" || normalized === "error";
}

function getClipCreationProgress(status: string | null) {
  const normalized = normalizeJobStatus(status);

  if (normalized === "done" || normalized === "completed") {
    return 100;
  }

  if (normalized === "failed" || normalized === "error") {
    return 100;
  }

  if (normalized === "processing" || normalized === "running" || normalized === "in_progress") {
    return 70;
  }

  return 20;
}

function formatJobStatusLabel(status: string | null) {
  const normalized = normalizeJobStatus(status);
  if (normalized === "done" || normalized === "completed") {
    return "Completado";
  }
  if (normalized === "failed" || normalized === "error") {
    return "Error";
  }
  if (normalized === "processing" || normalized === "running" || normalized === "in_progress") {
    return "Procesando";
  }
  return "En cola";
}

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return fallbackMessage;
}

export default function TimelinePage() {
  const searchParams = useSearchParams();
  const preferredVideoId = searchParams.get("videoId")?.trim() ?? "";
  const preferredClipId = searchParams.get("clipId")?.trim() ?? "";
  const token = useAuthStore((state) => state.token);
  const settings = useVideoSettingsStore((state) => state.settings);
  const [videos, setVideos] = useState<UserVideoItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [focusedClip, setFocusedClip] = useState<UserClipItem | null>(null);
  const [trimStart, setTrimStart] = useState(0);
  const [trimEnd, setTrimEnd] = useState(15);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitInfo, setSubmitInfo] = useState<string | null>(null);
  const [submitErrorSettings, setSubmitErrorSettings] = useState<string | null>(null);
  const [submitInfoSettings, setSubmitInfoSettings] = useState<string | null>(null);
  const [draftFilename, setDraftFilename] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJobStatus, setActiveJobStatus] = useState<string | null>(null);
  const [activeJobOutputPath, setActiveJobOutputPath] = useState<string | null>(null);
  const [activeJobPollingError, setActiveJobPollingError] = useState<string | null>(null);
  const [isPollingActiveJob, setIsPollingActiveJob] = useState(false);
  const [storedSession, setStoredSession] = useState<TimelineSession>(emptyTimelineSession);
  const [isSessionHydrated, setIsSessionHydrated] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(TIMELINE_SESSION_KEY);
      if (!raw) {
        setStoredSession(emptyTimelineSession);
        setIsSessionHydrated(true);
        return;
      }

      const parsed = JSON.parse(raw) as Partial<TimelineSession>;
      const next: TimelineSession = {
        lastVideoId: typeof parsed.lastVideoId === "string" ? parsed.lastVideoId : null,
        jobsByVideo:
          parsed.jobsByVideo && typeof parsed.jobsByVideo === "object"
            ? (parsed.jobsByVideo as Record<string, StoredTimelineJob>)
            : {}
      };
      setStoredSession(next);
    } catch {
      window.localStorage.removeItem(TIMELINE_SESSION_KEY);
      setStoredSession(emptyTimelineSession);
    } finally {
      setIsSessionHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!isSessionHydrated) {
      return;
    }

    window.localStorage.setItem(TIMELINE_SESSION_KEY, JSON.stringify(storedSession));
  }, [isSessionHydrated, storedSession]);


  const saveRaname = async () => {
    if (!token) {
      return;
    }

    if (!selectedVideoId) {
      setSubmitErrorSettings("Selecciona un video para guardar el nombre.");
      return;
    }

    setSubmitErrorSettings(null);
    setSubmitInfoSettings(null);
    try {
      const updated = await videoApi.updateMyVideo(selectedVideoId, token, { filename: draftFilename.trim() });
      setVideos((prev) => prev.map((item) => (item.video_id === selectedVideoId ? updated : item)));
      setSubmitInfoSettings("Ajustes guardados.");
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "No pudimos actualizar el nombre del video.";
      setSubmitErrorSettings(message);
    }
  };

  useEffect(() => {
    if (!isSessionHydrated) {
      return;
    }

    if (!token) {
      setIsLoading(false);
      setError("No encontramos una sesion activa para cargar el timeline.");
      return;
    }

    let cancelled = false;

    const loadVideos = async () => {
      setIsLoading(true);
      setError(null);
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

        const targetVideoId = preferredVideoFromQuery || selectedClip?.video_id || storedSession.lastVideoId || "";

        if (!targetVideoId) {
          setVideos([]);
          setFocusedClip(null);
          setSelectedVideoId(null);
          setDraftFilename("");
          setError("Selecciona un video desde Biblioteca para abrirlo en timeline.");
          return;
        }

        const preferredVideo = await videoApi.getMyVideoById(targetVideoId, token);
        if (cancelled) {
          return;
        }

        setVideos([
          {
            video_id: preferredVideo.video_id,
            filename: preferredVideo.filename,
            status: preferredVideo.status,
            uploaded_at: preferredVideo.uploaded_at,
            preview_url: preferredVideo.preview_url
          }
        ]);
        setFocusedClip(selectedClip);
        setSelectedVideoId(preferredVideo.video_id);
        setDraftFilename(preferredVideo.filename);
      } catch (loadError) {
        if (!cancelled) {
          setError(normalizeVideoError(loadError, "No pudimos cargar tus videos."));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadVideos();

    return () => {
      cancelled = true;
    };
  }, [token, preferredClipId, preferredVideoId, storedSession.lastVideoId, isSessionHydrated]);

  useEffect(() => {
    if (!selectedVideoId) {
      return;
    }

    setStoredSession((prev) => {
      if (prev.lastVideoId === selectedVideoId) {
        return prev;
      }

      return {
        ...prev,
        lastVideoId: selectedVideoId
      };
    });
  }, [selectedVideoId]);

  useEffect(() => {
    if (!selectedVideoId) {
      return;
    }

    const storedJob = storedSession.jobsByVideo[selectedVideoId];
    if (!storedJob) {
      setActiveJobId(null);
      setActiveJobStatus(null);
      setActiveJobOutputPath(null);
      setActiveJobPollingError(null);
      return;
    }

    setActiveJobId(storedJob.jobId);
    setActiveJobStatus(storedJob.status ?? null);
    setActiveJobOutputPath(storedJob.outputPath ?? null);
    setActiveJobPollingError(null);
  }, [selectedVideoId, storedSession.jobsByVideo]);

  useEffect(() => {
    if (!selectedVideoId || !activeJobId) {
      return;
    }

    setStoredSession((prev) => {
      const previousStoredJob = prev.jobsByVideo[selectedVideoId];
      const nextStoredJob: StoredTimelineJob = {
        jobId: activeJobId,
        status: activeJobStatus,
        outputPath: activeJobOutputPath,
        updatedAt: new Date().toISOString()
      };

      if (
        previousStoredJob &&
        previousStoredJob.jobId === nextStoredJob.jobId &&
        previousStoredJob.status === nextStoredJob.status &&
        previousStoredJob.outputPath === nextStoredJob.outputPath
      ) {
        return prev;
      }

      return {
        ...prev,
        jobsByVideo: {
          ...prev.jobsByVideo,
          [selectedVideoId]: nextStoredJob
        }
      };
    });
  }, [selectedVideoId, activeJobId, activeJobStatus, activeJobOutputPath]);

  const selectedVideo = useMemo(
    () => videos.find((video) => video.video_id === selectedVideoId) ?? null,
    [videos, selectedVideoId]
  );

  useEffect(() => {
    if (!selectedVideo) {
      return;
    }
    setDraftFilename(selectedVideo.filename);
  }, [selectedVideo]);

  const selectedPreviewUrl =
    focusedClip && focusedClip.video_id === selectedVideoId
      ? (focusedClip.output_path ?? selectedVideo?.preview_url ?? null)
      : (selectedVideo?.preview_url ?? null);

  const activeJobProgress = getClipCreationProgress(activeJobStatus);
  const activeJobStatusLabel = formatJobStatusLabel(activeJobStatus);

  useEffect(() => {
    if (!token || !activeJobId) {
      setIsPollingActiveJob(false);
      return;
    }

    let cancelled = false;

    const syncActiveJob = async () => {
      try {
        const status = await videoApi.getJobStatus(activeJobId, token);
        if (cancelled) {
          return;
        }

        setActiveJobStatus(status.status);
        setActiveJobOutputPath((prev) => prev ?? status.output_path ?? null);
        setActiveJobPollingError(null);
        const shouldContinuePolling = !isTerminalJobStatus(status.status) || !status.output_path;
        setIsPollingActiveJob(shouldContinuePolling);

        if (!shouldContinuePolling) {
          window.clearInterval(intervalId);
        }
      } catch (pollError) {
        if (!cancelled) {
          setActiveJobPollingError(normalizeVideoError(pollError, "No pudimos actualizar el estado del clip."));
        }
      }
    };

    setIsPollingActiveJob(true);
    const intervalId = window.setInterval(() => {
      void syncActiveJob();
    }, 4000);
    void syncActiveJob();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsPollingActiveJob(false);
    };
  }, [activeJobId, token]);

  const handleCreateJob = async () => {
    if (!token || !selectedVideoId) {
      setSubmitError("Selecciona un video y verifica tu sesion para crear el clip.");
      return;
    }

    const normalizedStart = Math.max(0, Math.floor(trimStart));
    const normalizedEnd = Math.max(normalizedStart + MIN_CLIP_SECONDS, Math.ceil(trimEnd));

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitInfo(null);

    try {
      const response = await videoApi.createReframeJob(selectedVideoId, token, {
        start_sec: normalizedStart,
        end_sec: normalizedEnd,
        subtitles: settings.subtitles,
        watermark: settings.watermark,
        output_style: settings.outputStyle,
        content_profile: settings.contentProfile
      });

      setSubmitInfo(`Clip enviado a cola. Job ${response.job_id.slice(0, 8)} en estado ${response.status}.`);
      setActiveJobId(response.job_id);
      setActiveJobStatus(response.status);
      setActiveJobOutputPath(null);
      setActiveJobPollingError(null);
    } catch (createError) {
      setSubmitError(normalizeVideoError(createError, "No pudimos crear el clip desde timeline."));
    } finally {
      setIsSubmitting(false);
    }
  };

  const videoEditarBool = !Boolean(preferredVideoId && preferredVideoId.trim().length > 0);

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">timeline</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Preview y recorte</h3>

          {videoEditarBool ? (
            <div className="mt-3 rounded-xl border border-neon-cyan/30 bg-neon-cyan/10 px-3 py-2 text-xs text-neon-cyan/90">
              Para cambiar de video, abrilo desde Biblioteca - Videos originales.
            </div>
          ) : null}
          {focusedClip ? (
            <div className="mt-3 rounded-xl border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-2 text-xs text-neon-cyan">
              Editando desde clip {focusedClip.job_id.slice(0, 8)} sobre video {focusedClip.video_id.slice(0, 8)}.
            </div>
          ) : null}

          {isLoading ? (
            <p className="mt-4 text-sm text-white/70">Cargando videos...</p>
          ) : error ? (
            <p className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>
          ) : selectedPreviewUrl ? (
            <VideoPreview
              videoPreviewUrl={selectedPreviewUrl}
              onTrimChange={(start, end) => {
                setTrimStart(start);
                setTrimEnd(end);
              }}
            />
          ) : (
            <p className="mt-4 text-sm text-white/70">
              Este video todavia no tiene URL de preview disponible. Prueba con otro video.
            </p>
          )}

          {activeJobId ? (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/80">Progreso de creacion del clip</span>
                <span className="text-white">{activeJobProgress}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-night-950/90">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-mint transition-all duration-700"
                  style={{ width: `${activeJobProgress}%` }}
                />
              </div>
              <p className="mt-2 text-xs text-white/65">
                Job {activeJobId.slice(0, 8)} - {activeJobStatusLabel}{isPollingActiveJob ? " (actualizando...)" : ""}
              </p>
              {activeJobPollingError ? <p className="mt-2 text-xs text-rose-200">{activeJobPollingError}</p> : null}

              <div className="mt-4">
                <p className="text-xs uppercase tracking-[0.16em] text-white/60">Preview final</p>
                {activeJobOutputPath ? (
                  <div className="mt-2 overflow-hidden rounded-xl border border-neon-cyan/30 bg-black">
                    <video controls preload="metadata" src={activeJobOutputPath} className="w-full max-h-[420px] bg-black" />
                  </div>
                ) : (
                  <div className="mt-2 rounded-xl border border-white/10 bg-night-900/70 px-3 py-4 text-sm text-white/70">
                    El preview final aparecera aca cuando termine el render.
                  </div>
                )}
              </div>
            </div>
          ) : null}



          {videoEditarBool && !selectedVideoId && !isLoading ? (
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
              <p>No hay video seleccionado para este timeline.</p>
              <Link
                href="/app/library"
                className="mt-3 inline-flex items-center justify-center rounded-lg border border-neon-cyan/40 bg-neon-cyan/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-neon-cyan transition hover:bg-neon-cyan/20"
              >
                Ir a Biblioteca
              </Link>
            </div>
          ) : null}
        </Panel>

        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">configuracion</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Ajustes de recorte</h3>
          <VideoSettings submitInfoSettings={submitInfoSettings} submitErrorSettings={submitErrorSettings} videoEditarBool={videoEditarBool} draftFilename={draftFilename} setDraftFilename={setDraftFilename} saveRaname={saveRaname} trimStart={trimStart} trimEnd={trimEnd} minClipDurationSec={MIN_CLIP_SECONDS} isSubmitting={isSubmitting} submitInfo={submitInfo} selectedVideoId={selectedVideoId} submitError={submitError}  handleCreateJob={handleCreateJob} />

          <div className="mt-4 rounded-xl border border-neon-violet/30 bg-neon-violet/5 p-3">
            <p className="text-xs uppercase tracking-[0.18em] text-neon-violet/85">Audio Editor</p>
            <p className="mt-2 text-xs text-white/75">
              La mezcla de audio ahora vive en una pantalla dedicada para trabajar por pistas.
            </p>
            <Link
              href={selectedVideoId ? `/app/audio_editor?videoId=${selectedVideoId}` : "/app/audio_editor"}
              className="mt-3 inline-flex w-full items-center justify-center rounded-lg border border-neon-violet/45 bg-neon-violet/15 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-neon-violet transition hover:bg-neon-violet/20"
            >
              Abrir Audio Editor
            </Link>
          </div>
        </Panel>
      </div>
    </section>
  );
}
