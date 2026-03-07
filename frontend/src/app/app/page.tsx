"use client";

import { GeneratedClipsSection, type Clip } from "@/src/components/home/GeneratedClipsSection";
import { ProjectStatusPanel } from "@/src/components/home/ProjectStatusPanel";
import { UploadDropzone } from "@/src/components/home/UploadDropzone";
import { Panel } from "@/src/components/ui/Panel";
import {
  type AudioUploadResponse,
  VideoApiError,
  type AutoReframeJobItem,
  type UserClipItem,
  type VideoUploadResponse,
  videoApi
} from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useLocale } from "next-intl";
import { useEffect, useMemo, useRef, useState } from "react";

const HOME_DRAFT_KEY = "home:uploaded-video-draft";
type ClipOutputStyle = "vertical" | "speaker_split";
type ClipContentProfile = "auto" | "interview" | "sports" | "music";
type UploadedMediaType = "video" | "audio";
type JobStatusInfo = {
  status: string;
  outputPath: string | null;
  subtitlesPath: string | null;
};

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
  jobStatusMap: Record<string, JobStatusInfo>,
  fallbackClips: UserClipItem[]
): Clip[] {
  const fallbackByJobId = new Map(fallbackClips.map((clip) => [clip.job_id, clip]));

  const mappedFromJobs = jobs.map((job, index) => {
    const statusInfo = jobStatusMap[job.job_id];
    const fallbackClip = fallbackByJobId.get(job.job_id);
    const status = statusInfo?.status ?? fallbackClip?.status ?? job.status;

    return {
      id: job.job_id,
      title: `Clip ${index + 1}`,
      duration: toTimeLabel(Math.max(job.end_sec - job.start_sec, 0)),
      preset: "Auto Reframe",
      status: mapJobStatusToClipStatus(status),
      previewUrl: statusInfo?.outputPath ?? fallbackClip?.output_path ?? null,
      subtitlesUrl: statusInfo?.subtitlesPath ?? null
    };
  });

  const knownIds = new Set(jobs.map((job) => job.job_id));
  const mappedFromLibraryOnly = fallbackClips
    .filter((clip) => !knownIds.has(clip.job_id))
    .map((clip, index) => ({
      id: clip.job_id,
      title: `Clip ${mappedFromJobs.length + index + 1}`,
      duration: "00:15",
      preset: "Auto Reframe",
      status: mapJobStatusToClipStatus(clip.status),
      previewUrl: clip.output_path
    }));

  return [...mappedFromJobs, ...mappedFromLibraryOnly];
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

function mapPendingSlotsToCards(total: number): Clip[] {
  const safeTotal = Math.max(total, 0);
  return Array.from({ length: safeTotal }, (_, index) => ({
    id: `pending-${index + 1}`,
    title: `Clip ${index + 1}`,
    duration: "00:15",
    preset: "Auto Reframe",
    status: "render",
    previewUrl: null,
    subtitlesUrl: null
  }));
}

function isTerminalStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed" || normalized === "failed" || normalized === "error";
}

function isDoneStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed";
}

function isFailedStatus(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "failed" || normalized === "error";
}

function isReframeClip(clip: UserClipItem) {
  const normalized = clip.job_type.toLowerCase();
  return normalized === "reframe";
}

function isAudioFile(file: File) {
  if (file.type.toLowerCase().startsWith("audio/")) {
    return true;
  }

  const lowerName = file.name.toLowerCase();
  return [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma", ".opus"].some((ext) => lowerName.endsWith(ext));
}

function normalizeVideoError(error: unknown, fallbackMessage: string, isEn: boolean) {
  if (error instanceof VideoApiError) {
    if (error.status === 400) {
      return error.message || (isEn ? "The file is invalid or does not meet requirements." : "El archivo es invalido o no cumple los requisitos.");
    }

    if (error.status === 401) {
      return isEn ? "Your session expired. Please sign in again." : "Tu sesion expiro. Vuelve a iniciar sesion para continuar.";
    }

    return error.message;
  }

  if (error instanceof Error) {
    const normalizedMessage = error.message.toLowerCase();
    if (normalizedMessage.includes("failed to fetch") || normalizedMessage.includes("networkerror")) {
      return isEn
        ? "We could not connect to the server. Please try again in a few seconds."
        : "No pudimos conectar con el servidor. Intenta de nuevo en unos segundos.";
    }

    return error.message;
  }

  return fallbackMessage;
}

export default function AppHomePage() {
  const locale = useLocale();
  const isEn = locale === "en";
  const token = useAuthStore((state) => state.token);
  const [isUploading, setIsUploading] = useState(false);
  const [isCreatingJobs, setIsCreatingJobs] = useState(false);
  const [isPollingStatuses, setIsPollingStatuses] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<VideoUploadResponse | null>(null);
  const [uploadedAudio, setUploadedAudio] = useState<AudioUploadResponse | null>(null);
  const [uploadedMediaType, setUploadedMediaType] = useState<UploadedMediaType | null>(null);
  const [autoJobCount, setAutoJobCount] = useState(0);
  const [createdJobs, setCreatedJobs] = useState<AutoReframeJobItem[]>([]);
  const [jobStatusMap, setJobStatusMap] = useState<Record<string, JobStatusInfo>>({});
  const [orchestratorJobId, setOrchestratorJobId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [isHydratingClips, setIsHydratingClips] = useState(false);
  const [outputStyle, setOutputStyle] = useState<ClipOutputStyle>("vertical");
  const [contentProfile, setContentProfile] = useState<ClipContentProfile>("auto");
  const [withSubtitles, setWithSubtitles] = useState(false);
  const [watermark, setWatermark] = useState("Hacelo Corto");
  const [fallbackClips, setFallbackClips] = useState<UserClipItem[]>([]);
  const jobStatusMapRef = useRef<Record<string, JobStatusInfo>>({});

  useEffect(() => {
    jobStatusMapRef.current = jobStatusMap;
  }, [jobStatusMap]);

  const hasVideo = Boolean(uploadedVideo);
  const hasAudio = Boolean(uploadedAudio);
  const visibleClips = useMemo(() => {
    const reframeFallbackClips = fallbackClips.filter(isReframeClip);
    if (createdJobs.length > 0) {
      return mapJobsToClips(createdJobs, jobStatusMap, reframeFallbackClips);
    }

    if (autoJobCount > 0 && reframeFallbackClips.length === 0) {
      return mapPendingSlotsToCards(autoJobCount);
    }

    return mapUserClipsToCards(reframeFallbackClips);
  }, [createdJobs, jobStatusMap, fallbackClips, autoJobCount]);

  const clipProgress = useMemo(() => {
    const statusByJob = new Map<string, string>();

    createdJobs.forEach((job) => {
      const status = jobStatusMap[job.job_id]?.status ?? job.status;
      statusByJob.set(job.job_id, status);
    });

    fallbackClips.forEach((clip) => {
      const current = statusByJob.get(clip.job_id);
      if (!current || (!isTerminalStatus(current) && isTerminalStatus(clip.status))) {
        statusByJob.set(clip.job_id, clip.status);
      }
    });

    const statuses = Array.from(statusByJob.values());
    const done = statuses.filter((status) => isDoneStatus(status)).length;
    const failed = statuses.filter((status) => isFailedStatus(status)).length;
    const total = autoJobCount > 0 ? autoJobCount : statuses.length;
    const pending = Math.max(total - done - failed, 0);
    const percent = total > 0 ? Math.round(((done + failed) / total) * 100) : 0;

    return {
      done,
      failed,
      pending,
      total,
      percent
    };
  }, [autoJobCount, createdJobs, fallbackClips, jobStatusMap]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(HOME_DRAFT_KEY);
      if (!raw) {
        return;
      }

      const parsed = JSON.parse(raw) as {
        uploadedVideo: VideoUploadResponse | null;
        uploadedAudio?: AudioUploadResponse | null;
        uploadedMediaType?: UploadedMediaType | null;
        createdJobs: AutoReframeJobItem[];
        autoJobCount: number;
        orchestratorJobId?: string | null;
        outputStyle?: ClipOutputStyle;
        contentProfile?: ClipContentProfile;
        withSubtitles?: boolean;
        watermark?: string;
      };

      if (parsed.uploadedVideo) {
        setUploadedVideo(parsed.uploadedVideo);
      }
      if (parsed.uploadedAudio) {
        setUploadedAudio(parsed.uploadedAudio);
      }
      if (parsed.uploadedMediaType === "video" || parsed.uploadedMediaType === "audio") {
        setUploadedMediaType(parsed.uploadedMediaType);
      }
      if (Array.isArray(parsed.createdJobs)) {
        setCreatedJobs(parsed.createdJobs);
      }
      if (typeof parsed.autoJobCount === "number") {
        setAutoJobCount(parsed.autoJobCount);
      }
      if (typeof parsed.orchestratorJobId === "string") {
        setOrchestratorJobId(parsed.orchestratorJobId);
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
      if (typeof parsed.withSubtitles === "boolean") {
        setWithSubtitles(parsed.withSubtitles);
      }
      if (typeof parsed.watermark === "string") {
        setWatermark(parsed.watermark);
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
      uploadedAudio,
      uploadedMediaType,
      createdJobs,
      autoJobCount,
      orchestratorJobId,
      outputStyle,
      contentProfile,
      withSubtitles,
      watermark
    };

    window.localStorage.setItem(HOME_DRAFT_KEY, JSON.stringify(payload));
  }, [uploadedVideo, uploadedAudio, uploadedMediaType, createdJobs, autoJobCount, orchestratorJobId, outputStyle, contentProfile, withSubtitles, watermark]);

  useEffect(() => {
    if (!token || (createdJobs.length === 0 && !orchestratorJobId)) {
      setIsPollingStatuses(false);
      return;
    }

    let cancelled = false;

    const syncStatuses = async () => {
      try {
        let jobIds = createdJobs.map((job) => job.job_id);

        if (jobIds.length === 0 && orchestratorJobId) {
          const orchestratorStatus = await videoApi.getJobStatus(orchestratorJobId, token);
          if (cancelled) {
            return;
          }

          if (orchestratorStatus.child_jobs.length > 0) {
            jobIds = Array.from(new Set([...jobIds, ...orchestratorStatus.child_jobs]));
            setAutoJobCount((prev) => Math.max(prev, orchestratorStatus.child_jobs.length));
            setCreatedJobs((prev) => {
              const existingById = new Map(prev.map((job) => [job.job_id, job]));
              orchestratorStatus.child_jobs.forEach((jobId, index) => {
                if (!existingById.has(jobId)) {
                  existingById.set(jobId, {
                    job_id: jobId,
                    job_type: "AUTO_REFRAME",
                    status: "PENDING",
                    start_sec: index * 15,
                    end_sec: (index + 1) * 15,
                    created_at: new Date().toISOString()
                  });
                }
              });

              const merged = Array.from(existingById.values());
              if (merged.length === prev.length) {
                return prev;
              }

              return merged;
            });
          } else {
            const isOrchestratorOpen = !isTerminalStatus(orchestratorStatus.status);
            setIsPollingStatuses(isOrchestratorOpen);
            if (!isOrchestratorOpen) {
              window.clearInterval(intervalId);
            }
            return;
          }
        }

        const jobsToPoll = jobIds.filter((jobId) => {
          const cached = jobStatusMapRef.current[jobId];
          if (!cached) {
            return true;
          }

          return !isTerminalStatus(cached.status) || !cached.outputPath;
        });

        if (jobsToPoll.length === 0) {
          setIsPollingStatuses(false);
          window.clearInterval(intervalId);
          return;
        }

        const statuses = await Promise.all(jobsToPoll.map((jobId) => videoApi.getJobStatus(jobId, token)));
        if (cancelled) {
          return;
        }

        let shouldContinuePolling = false;

        setJobStatusMap((prev) => {
          const nextMap: Record<string, JobStatusInfo> = { ...prev };

          statuses.forEach((item) => {
            const previous = prev[item.job_id];
            const stableOutputPath = item.output_path ?? previous?.outputPath ?? null;
            const stableSubtitlesPath = item.subtitles_path ?? previous?.subtitlesPath ?? null;
            nextMap[item.job_id] = {
              status: item.status,
              outputPath: stableOutputPath,
              subtitlesPath: stableSubtitlesPath
            };

            const waitingForOutput = !stableOutputPath && (item.status.toLowerCase() === "done" || item.status.toLowerCase() === "completed");
            if (!isTerminalStatus(item.status) || waitingForOutput) {
              shouldContinuePolling = true;
            }
          });

          const hasDiff = statuses.some((item) => {
            const jobId = item.job_id;
            const current = prev[jobId];
            const next = nextMap[jobId];
            return !current || current.status !== next.status || current.outputPath !== next.outputPath || current.subtitlesPath !== next.subtitlesPath;
          });
          return hasDiff ? nextMap : prev;
        });

        if (!shouldContinuePolling) {
          window.clearInterval(intervalId);
        }

        setIsPollingStatuses(shouldContinuePolling);
      } catch {
        if (!cancelled) {
          setJobError((prev) => prev ?? (isEn ? "We could not refresh some generated clip statuses." : "No pudimos actualizar el estado de algunos clips generados."));
        }
      }
    };

    setIsPollingStatuses(true);
    const intervalId = window.setInterval(() => {
      void syncStatuses();
    }, 7000);
    void syncStatuses();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsPollingStatuses(false);
    };
  }, [createdJobs, orchestratorJobId, token, isEn]);

  const handleUpload = async (file: File) => {
    const isAudio = isAudioFile(file);

    setIsUploading(true);
    setIsCreatingJobs(false);
    setUploadedVideo(null);
    setUploadedAudio(null);
    setUploadedMediaType(isAudio ? "audio" : "video");
    setCreatedJobs([]);
    setFallbackClips([]);
    setJobStatusMap({});
    setAutoJobCount(0);
    setOrchestratorJobId(null);
    setUploadError(null);
    setJobError(null);
    window.localStorage.removeItem(HOME_DRAFT_KEY);

    let uploadedVideoResponse: VideoUploadResponse | null = null;
    let uploadedAudioResponse: AudioUploadResponse | null = null;

    try {
      if (isAudio) {
        uploadedAudioResponse = await videoApi.uploadAudio(file, token);
      } else {
        uploadedVideoResponse = await videoApi.upload(file, token);
      }
    } catch (error) {
      setUploadError(normalizeVideoError(error, isEn ? "We could not upload the file." : "No pudimos subir el archivo.", isEn));
      setIsUploading(false);
      return;
    }

    if (uploadedAudioResponse) {
      setUploadedAudio(uploadedAudioResponse);
      setUploadedVideo(null);
      setIsUploading(false);
      return;
    }

    if (!uploadedVideoResponse) {
      setUploadError(isEn ? "We could not determine the uploaded file type." : "No pudimos determinar el tipo de archivo subido.");
      setIsUploading(false);
      return;
    }

    setUploadedVideo(uploadedVideoResponse);
    setIsUploading(false);

    if (!token) {
      setJobError(isEn ? "No active session found to create automatic clips. Please sign in again." : "No encontramos tu sesion para crear clips automaticos. Volve a iniciar sesion.");
      return;
    }

    setIsCreatingJobs(true);

    try {
      const autoJobs = await videoApi.createAutoReframeJobs(uploadedVideoResponse.video_id, token, {
        outputStyle,
        contentProfile,
        subtitles: withSubtitles,
        watermark
      });
      setCreatedJobs(autoJobs.jobs);
      setAutoJobCount(autoJobs.total_jobs);
      setOrchestratorJobId(autoJobs.orchestrator_job_id ?? null);

      const initialMap: Record<string, JobStatusInfo> = {};
      autoJobs.jobs.forEach((job) => {
        initialMap[job.job_id] = { status: job.status, outputPath: null, subtitlesPath: null };
      });
      setJobStatusMap(initialMap);
    } catch (error) {
      setJobError(normalizeVideoError(error, isEn ? "We could not create automatic clips." : "No pudimos crear los clips automaticos.", isEn));
    } finally {
      setIsCreatingJobs(false);
    }
  };

  useEffect(() => {
    if (!token || !uploadedVideo) {
      setIsHydratingClips(false);
      return;
    }

    const hasPendingTrackedJobs =
      createdJobs.length > 0 &&
      createdJobs.some((job) => {
        const status = jobStatusMap[job.job_id]?.status ?? job.status;
        return !isTerminalStatus(status);
      });

    const shouldHydrateFromLibrary =
      !isUploading &&
      !isCreatingJobs &&
      (createdJobs.length === 0 || hasPendingTrackedJobs || (autoJobCount > 0 && fallbackClips.length < autoJobCount));

    if (!shouldHydrateFromLibrary) {
      setIsHydratingClips(false);
      return;
    }

    let cancelled = false;
    let attempts = 0;
    const maxAttempts = 8;

    const hydrateFromLibrary = async () => {
      try {
        attempts += 1;
        const data = await videoApi.getMyClips(token, { limit: 40, offset: 0 });
        if (cancelled) {
          return;
        }

        const related = data.clips.filter((clip) => clip.video_id === uploadedVideo.video_id && isReframeClip(clip));
        setFallbackClips(related);
        setAutoJobCount((prev) => (prev > 0 ? prev : related.length));

        const expectedClips = autoJobCount > 0 ? autoJobCount : null;
        const reachedExpectedCount = expectedClips !== null && related.length >= expectedClips;
        if (reachedExpectedCount) {
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
    }, 12000);
    void hydrateFromLibrary();

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
      setIsHydratingClips(false);
    };
  }, [token, uploadedVideo, createdJobs, jobStatusMap, isUploading, isCreatingJobs, autoJobCount, fallbackClips.length]);

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.95fr]">
        <Panel variant="accent" className="p-4 sm:p-5">
          <div className="mb-4 rounded-xl border border-white/12 bg-white/5 p-3">
            <p className="text-xs uppercase tracking-[0.18em] text-white/60">{isEn ? "Processing options" : "Opciones de procesamiento"}</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_auto] sm:items-center">
              <label className="flex items-center justify-between rounded-lg border border-white/15 bg-night-900/70 px-3 py-2 text-sm text-white/85">
                <span>{isEn ? "Automatic subtitles" : "Subtitulos automaticos"}</span>
                <input
                  type="checkbox"
                  checked={withSubtitles}
                  onChange={(event) => setWithSubtitles(event.target.checked)}
                  className="h-4 w-4 rounded border-white/20 bg-night-900 text-neon-cyan focus:ring-neon-cyan"
                />
              </label>
              <label className="rounded-lg border border-white/15 bg-night-900/70 px-3 py-2 text-sm text-white/85">
                <span className="mr-2 text-xs uppercase tracking-[0.12em] text-white/55">Watermark</span>
                <input
                  value={watermark}
                  onChange={(event) => setWatermark(event.target.value.slice(0, 12))}
                  maxLength={12}
                  className="mt-1 w-full rounded-md border border-white/20 bg-night-900/80 px-2 py-1.5 text-sm text-white outline-none focus:border-neon-cyan/50"
                />
              </label>
            </div>

            <p className="mt-4 text-xs uppercase tracking-[0.18em] text-white/60">{isEn ? "Clip style" : "Estilo de clip"}</p>
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
                {isEn ? "Classic vertical 9:16" : "Vertical clasico 9:16"}
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
                {isEn ? "Speaker split (focus top, wide shot bottom)" : "Split speaker (arriba foco, abajo plano general)"}
              </button>
            </div>

            <div className="mt-3">
               <p className="text-xs uppercase tracking-[0.18em] text-white/55">{isEn ? "Content profile (auto in Home)" : "Perfil de contenido (auto en Home)"}</p>
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
                   {isEn ? "Auto detect" : "Auto detectar"}
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
                   {isEn ? "Interview" : "Entrevista"}
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
                   {isEn ? "Sports" : "Deportes"}
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
                   {isEn ? "Music" : "Musica"}
                </button>
              </div>
            </div>

            {outputStyle === "speaker_split" && (
              <div className="mt-3">
                 <p className="text-xs uppercase tracking-[0.18em] text-white/55">{isEn ? "Speaker split layout tweak" : "Ajuste de layout speaker split"}</p>
                 <div className="mt-2 text-xs text-white/70">
                   {isEn
                     ? "In `Auto detect`, if backend classifies as `sports`, it applies a wider framing."
                     : "En `Auto detectar`, si el backend clasifica como `deportes`, aplica framing mas abierto."}
                 </div>
              </div>
            )}
          </div>
          <UploadDropzone
            onUpload={handleUpload}
            isUploading={isUploading}
            fileName={uploadedVideo?.filename ?? uploadedAudio?.filename}
            fileKind={uploadedMediaType ?? (uploadedAudio ? "audio" : "video")}
          />
          {hasAudio ? (
            <div className="mt-4 rounded-xl border border-neon-mint/35 bg-neon-mint/10 p-3 text-xs text-neon-mint">
              {isEn
                ? "Audio uploaded successfully. You can now find it in Library - Audios and use it in upcoming mixing flows."
                : "Audio cargado correctamente. Ya podes verlo en Biblioteca - Audios y usarlo en los proximos flujos de mezcla."}
            </div>
          ) : null}
        </Panel>

        <Panel>
          <ProjectStatusPanel
            hasVideo={hasVideo}
            hasAudio={hasAudio}
            isUploading={isUploading}
            uploadError={uploadError}
            isCreatingJobs={isCreatingJobs}
            jobsCreated={autoJobCount}
            clipsPending={clipProgress.pending}
            clipProgressPercent={clipProgress.percent}
            jobError={jobError}
          />
        </Panel>
      </div>
      <Panel className="mt-5">
        <GeneratedClipsSection
          clips={visibleClips}
          showLoading={
            uploadedMediaType !== "audio" &&
            (isUploading || (isCreatingJobs && createdJobs.length === 0) || (isHydratingClips && visibleClips.length === 0))
          }
          isRefreshingStatuses={isPollingStatuses}
          emptyMessage={
            uploadedMediaType === "audio"
              ? (isEn ? "You uploaded audio. Clips are generated when you upload a video in this panel." : "Subiste un audio. Los clips se generan cuando subis un video en este panel.")
              : (isEn ? "No clips generated yet. Upload a video to start." : "Todavia no hay clips generados. Subi un video para empezar.")
          }
        />
      </Panel>
    </section>
  );
}
