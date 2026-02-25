"use client";

import { GeneratedClipsSection, type Clip } from "@/src/components/home/GeneratedClipsSection";
import { ProjectStatusPanel } from "@/src/components/home/ProjectStatusPanel";
import { UploadDropzone } from "@/src/components/home/UploadDropzone";
import { Panel } from "@/src/components/ui/Panel";
import {
  VideoApiError,
  type AutoReframeJobItem,
  type UserClipItem,
  type VideoUploadResponse,
  videoApi
} from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useEffect, useMemo, useState } from "react";

const HOME_DRAFT_KEY = "home:uploaded-video-draft";
type ClipOutputStyle = "vertical" | "speaker_split";
type ClipContentProfile = "auto" | "interview" | "sports" | "music";

function toTimeLabel(seconds: number) {
  const min = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const sec = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${min}:${sec}`;
}

function mapJobStatusToClipStatus(status: string): Clip["status"] {
  const normalized = status.toLowerCase();
  if (normalized === "completed" || normalized === "done") {
    return "listo";
  }

  if (normalized === "failed" || normalized === "error") {
    return "revision";
  }

  return "render";
}

function mapJobsToClips(
  jobs: AutoReframeJobItem[],
  jobStatusMap: Record<string, { status: string; outputPath: string | null }>
): Clip[] {
  return jobs.map((job, index) => {
    const statusInfo = jobStatusMap[job.job_id];
    const status = statusInfo?.status ?? job.status;

    return {
      id: job.job_id,
      title: `Clip ${index + 1}`,
      duration: toTimeLabel(Math.max(job.end_sec - job.start_sec, 0)),
      preset: "Auto Reframe",
      status: mapJobStatusToClipStatus(status),
      previewUrl: statusInfo?.outputPath ?? null
    };
  });
}

function mapUserClipsToCards(clips: UserClipItem[]): Clip[] {
  return clips.map((clip, index) => ({
    id: clip.job_id,
    title: `Clip ${index + 1}`,
    duration: "00:15",
    preset: "Auto Reframe",
    status: mapJobStatusToClipStatus(clip.status),
    previewUrl: clip.output_path
  }));
}

function isTerminalStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed" || normalized === "failed" || normalized === "error";
}

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    if (error.status === 400) {
      return "El archivo de video es invalido o no cumple los requisitos.";
    }

    if (error.status === 401) {
      return "Tu sesion expiro. Vuelve a iniciar sesion para continuar.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    const normalizedMessage = error.message.toLowerCase();
    if (normalizedMessage.includes("failed to fetch") || normalizedMessage.includes("networkerror")) {
      return "No pudimos conectar con el servidor. Intenta de nuevo en unos segundos.";
    }

    return error.message;
  }

  return fallbackMessage;
}

export default function AppHomePage() {
  const token = useAuthStore((state) => state.token);
  const [isUploading, setIsUploading] = useState(false);
  const [isCreatingJobs, setIsCreatingJobs] = useState(false);
  const [isPollingStatuses, setIsPollingStatuses] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResponse | null>(null);
  const [autoJobCount, setAutoJobCount] = useState(0);
  const [createdJobs, setCreatedJobs] = useState<AutoReframeJobItem[]>([]);
  const [jobStatusMap, setJobStatusMap] = useState<Record<string, { status: string; outputPath: string | null }>>({});
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [isHydratingClips, setIsHydratingClips] = useState(false);
  const [outputStyle, setOutputStyle] = useState<ClipOutputStyle>("vertical");
  const [contentProfile, setContentProfile] = useState<ClipContentProfile>("auto");
  const [fallbackClips, setFallbackClips] = useState<UserClipItem[]>([]);

  const hasVideo = Boolean(uploadedVideo);
  const visibleClips = useMemo(() => {
    if (createdJobs.length > 0) {
      return mapJobsToClips(createdJobs, jobStatusMap);
    }
    return mapUserClipsToCards(fallbackClips);
  }, [createdJobs, jobStatusMap, fallbackClips]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(HOME_DRAFT_KEY);
      if (!raw) {
        return;
      }

      const parsed = JSON.parse(raw) as {
        uploadedVideo: VideoUploadResponse | null;
        createdJobs: AutoReframeJobItem[];
        autoJobCount: number;
        outputStyle?: ClipOutputStyle;
        contentProfile?: ClipContentProfile;
      };

      if (parsed.uploadedVideo) {
        setUploadedVideo(parsed.uploadedVideo);
      }
      if (Array.isArray(parsed.createdJobs)) {
        setCreatedJobs(parsed.createdJobs);
      }
      if (typeof parsed.autoJobCount === "number") {
        setAutoJobCount(parsed.autoJobCount);
      }
      if (parsed.outputStyle === "vertical" || parsed.outputStyle === "speaker_split") {
        setOutputStyle(parsed.outputStyle);
      }
      if (
        parsed.contentProfile === "auto" ||
        parsed.contentProfile === "interview" ||
        parsed.contentProfile === "sports" ||
        parsed.contentProfile === "music"
      ) {
        setContentProfile(parsed.contentProfile);
      }
    } catch {
      window.localStorage.removeItem(HOME_DRAFT_KEY);
    }
  }, []);

  useEffect(() => {
    if (!uploadedVideo) {
      window.localStorage.removeItem(HOME_DRAFT_KEY);
      return;
    }

    const payload = {
      uploadedVideo,
      createdJobs,
      autoJobCount,
      outputStyle,
      contentProfile
    };

    window.localStorage.setItem(HOME_DRAFT_KEY, JSON.stringify(payload));
  }, [uploadedVideo, createdJobs, autoJobCount, outputStyle, contentProfile]);

  useEffect(() => {
    if (!token || createdJobs.length === 0) {
      setIsPollingStatuses(false);
      return;
    }

    let cancelled = false;

    const syncStatuses = async () => {
      try {
        const statuses = await Promise.all(createdJobs.map((job) => videoApi.getJobStatus(job.job_id, token)));
        if (cancelled) {
          return;
        }

        let shouldContinuePolling = false;

        setJobStatusMap((prev) => {
          const nextMap: Record<string, { status: string; outputPath: string | null }> = {};

          statuses.forEach((item) => {
            const previous = prev[item.job_id];
            const stableOutputPath = previous?.outputPath ?? item.output_path ?? null;
            nextMap[item.job_id] = {
              status: item.status,
              outputPath: stableOutputPath
            };

            const waitingForOutput = !stableOutputPath && (item.status.toLowerCase() === "done" || item.status.toLowerCase() === "completed");
            if (!isTerminalStatus(item.status) || waitingForOutput) {
              shouldContinuePolling = true;
            }
          });

          const hasDiff = JSON.stringify(prev) !== JSON.stringify(nextMap);
          return hasDiff ? nextMap : prev;
        });

        if (!shouldContinuePolling) {
          window.clearInterval(intervalId);
        }

        setIsPollingStatuses(shouldContinuePolling);
      } catch {
        if (!cancelled) {
          setJobError((prev) => prev ?? "No pudimos actualizar el estado de algunos clips generados.");
        }
      }
    };

    setIsPollingStatuses(true);
    const intervalId = window.setInterval(() => {
      void syncStatuses();
    }, 6000);
    void syncStatuses();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsPollingStatuses(false);
    };
  }, [createdJobs, token]);

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setIsCreatingJobs(false);
    setUploadedVideo(null);
    setCreatedJobs([]);
    setFallbackClips([]);
    setJobStatusMap({});
    setAutoJobCount(0);
    setUploadError(null);
    setJobError(null);
    window.localStorage.removeItem(HOME_DRAFT_KEY);

    let uploaded: VideoUploadResponse;

    try {
      uploaded = await videoApi.upload(file, token);
    } catch (error) {
      setUploadError(normalizeVideoError(error, "No pudimos subir el video."));
      setIsUploading(false);
      return;
    }

    setUploadedVideo(uploaded);
    setIsUploading(false);

    if (!token) {
      setJobError("No encontramos tu sesion para crear clips automaticos. Volve a iniciar sesion.");
      return;
    }

    setIsCreatingJobs(true);

    try {
      const autoJobs = await videoApi.createAutoReframeJobs(uploaded.video_id, token, {
        outputStyle,
        contentProfile
      });
      setCreatedJobs(autoJobs.jobs);
      setAutoJobCount(autoJobs.total_jobs);

      const initialMap: Record<string, { status: string; outputPath: string | null }> = {};
      autoJobs.jobs.forEach((job) => {
        initialMap[job.job_id] = { status: job.status, outputPath: null };
      });
      setJobStatusMap(initialMap);
    } catch (error) {
      setJobError(normalizeVideoError(error, "No pudimos crear los clips automaticos."));
    } finally {
      setIsCreatingJobs(false);
    }
  };

  useEffect(() => {
    if (!token || !uploadedVideo || createdJobs.length > 0 || isUploading || isCreatingJobs) {
      setIsHydratingClips(false);
      return;
    }

    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 20;

    const hydrateFromLibrary = async () => {
      try {
        attempts += 1;
        const data = await videoApi.getMyClips(token, { limit: 40, offset: 0 });
        if (cancelled) {
          return;
        }

        const related = data.clips.filter((clip) => clip.video_id === uploadedVideo.video_id);
        if (related.length > 0) {
          setFallbackClips(related);
          setAutoJobCount((prev) => (prev > 0 ? prev : related.length));
          setIsHydratingClips(false);
          window.clearInterval(intervalId);
          return;
        }

        if (attempts >= maxAttempts) {
          setIsHydratingClips(false);
          window.clearInterval(intervalId);
        }
      } catch {
        // Silencioso: este hydrate es best-effort para evitar estados vacios en Home.
      }
    };

    setIsHydratingClips(true);
    const intervalId = window.setInterval(() => {
      void hydrateFromLibrary();
    }, 5000);
    void hydrateFromLibrary();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsHydratingClips(false);
    };
  }, [token, uploadedVideo, createdJobs.length, isUploading, isCreatingJobs]);

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel variant="accent" className="p-4 sm:p-5">
          <div className="mb-4 rounded-xl border border-white/12 bg-white/5 p-3">
            <p className="text-xs uppercase tracking-[0.18em] text-white/60">Estilo de clip</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              <button
                type="button"
                onClick={() => setOutputStyle("vertical")}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                  outputStyle === "vertical"
                    ? "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
                    : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                }`}
              >
                Vertical clasico 9:16
              </button>
              <button
                type="button"
                onClick={() => setOutputStyle("speaker_split")}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                  outputStyle === "speaker_split"
                    ? "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
                    : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                }`}
              >
                Split speaker (arriba foco, abajo plano general)
              </button>
            </div>

            <div className="mt-3">
              <p className="text-xs uppercase tracking-[0.18em] text-white/55">Perfil de contenido (auto en Home)</p>
              <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                <button
                  type="button"
                  onClick={() => setContentProfile("auto")}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                    contentProfile === "auto"
                      ? "border-neon-mint/45 bg-neon-mint/15 text-neon-mint"
                      : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                  }`}
                >
                  Auto detectar
                </button>
                <button
                  type="button"
                  onClick={() => setContentProfile("interview")}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                    contentProfile === "interview"
                      ? "border-neon-mint/45 bg-neon-mint/15 text-neon-mint"
                      : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                  }`}
                >
                  Entrevista
                </button>
                <button
                  type="button"
                  onClick={() => setContentProfile("sports")}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                    contentProfile === "sports"
                      ? "border-neon-mint/45 bg-neon-mint/15 text-neon-mint"
                      : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                  }`}
                >
                  Deportes
                </button>
                <button
                  type="button"
                  onClick={() => setContentProfile("music")}
                  className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                    contentProfile === "music"
                      ? "border-neon-mint/45 bg-neon-mint/15 text-neon-mint"
                      : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                  }`}
                >
                  Musica
                </button>
              </div>
            </div>

            {outputStyle === "speaker_split" && (
              <div className="mt-3">
                <p className="text-xs uppercase tracking-[0.18em] text-white/55">Ajuste de layout speaker split</p>
                <div className="mt-2 text-xs text-white/70">
                  En `Auto detectar`, si el backend clasifica como `deportes`, aplica framing mas abierto.
                </div>
              </div>
            )}
          </div>
          <UploadDropzone
            onUpload={handleUpload}
            isUploading={isUploading}
            fileName={uploadedVideo?.filename}
          />
        </Panel>

        <Panel>
          <ProjectStatusPanel
            hasVideo={hasVideo}
            isUploading={isUploading}
            uploadError={uploadError}
            videoId={uploadedVideo?.video_id ?? null}
            isCreatingJobs={isCreatingJobs}
            jobsCreated={autoJobCount}
            jobError={jobError}
          />
        </Panel>
      </div>
      <Panel className="mt-5">
        <GeneratedClipsSection
          clips={visibleClips}
          showLoading={isUploading || (isCreatingJobs && createdJobs.length === 0) || (isHydratingClips && visibleClips.length === 0)}
          isRefreshingStatuses={isPollingStatuses}
        />
      </Panel>
    </section>
  );
}
