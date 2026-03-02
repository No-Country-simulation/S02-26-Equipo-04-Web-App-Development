"use client";

import { VideoSettings } from "@/src/components/home/VideoSettings";
import { VideoPreview } from "@/src/components/home/videoPrevewTimeLine/VideoPreview";
import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserClipItem, type UserVideoItem, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useVideoSettingsStore } from "@/src/store/useVideoSettingsStore";
import { Search } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 10;
const MIN_CLIP_SECONDS = 5;

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
  const [totalVideos, setTotalVideos] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
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


  const saveRaname =  async()=>{
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

  }

  useEffect(() => {
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

        const response = await videoApi.getMyVideos(token, {
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
          query
        });
        if (cancelled) {
          return;
        }

        let nextVideos = response.videos;

        if (preferredVideoFromQuery && !response.videos.some((video) => video.video_id === preferredVideoFromQuery)) {
          try {
            const preferredVideo = await videoApi.getMyVideoById(preferredVideoFromQuery, token);
            nextVideos = [
              {
                video_id: preferredVideo.video_id,
                filename: preferredVideo.filename,
                status: preferredVideo.status,
                uploaded_at: preferredVideo.uploaded_at,
                preview_url: preferredVideo.preview_url
              },
              ...response.videos.filter((video) => video.video_id !== preferredVideo.video_id)
            ];
          } catch {
            nextVideos = response.videos;
          }
        }

        setVideos(nextVideos);
        setFocusedClip(selectedClip);
        setDraftFilename(selectedClip?.source_filename || "")
        setTotalVideos(response.total);
        setSelectedVideoId((prev) => {
          if (preferredVideoFromQuery && nextVideos.some((video) => video.video_id === preferredVideoFromQuery)) {
            return preferredVideoFromQuery;
          }
          if (prev && nextVideos.some((video) => video.video_id === prev)) {
            return prev;
          }
          return nextVideos[0]?.video_id ?? null;
        });
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
  }, [token, page, preferredClipId, preferredVideoId, query]);

  const totalPages = Math.max(1, Math.ceil(totalVideos / PAGE_SIZE));

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
        crop_to_vertical: settings.cropToVertical,
        subtitles: settings.subtitles,
        watermark: settings.watermark,
        face_tracking: settings.faceTracking,
        color_filter: settings.colorFilter
      });

      setSubmitInfo(`Clip enviado a cola. Job ${response.job_id.slice(0, 8)} en estado ${response.status}.`);
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
          {videoEditarBool &&(<label className="mt-3 flex items-center gap-2 rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-white/80 transition hover:border-neon-cyan/40">
            <Search size={14} className="text-neon-cyan/80" />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
              placeholder="Buscar clip por job o archivo..."
              className="w-full bg-transparent text-sm text-white/90 outline-none placeholder:text-white/40"
            />
          </label>
)}
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



          {
          // !videoEditarBool&&(
          //   <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
          //     <label className="">
          //       Nombre
          //     </label>
          //     <input
          //         value={draftFilename}
          //         onChange={(event) => setDraftFilename(event.target.value)}
          //         className="w-full rounded-lg border border-white/20 bg-night-900/70 px-3 mt-1 py-2 text-xs text-white outline-none transition focus:border-neon-cyan/50"
          //         maxLength={255}
          //         autoFocus
          //         />
          //         {/* <Button className="mt-3 w-auto px-4" disabled={isSubmitting || !selectedVideoId}>
          //         Guardar Cambios
          //       </Button> */}
          // </div>)
          
          }

          
          {/* <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
            <p>Recorte seleccionado: {Math.floor(trimStart)}s - {Math.ceil(trimEnd)}s</p>
            <Button className="mt-3 w-auto px-4" onClick={handleCreateJob} disabled={isSubmitting || !selectedVideoId}>
              {isSubmitting ? "Creando clip..." : "Generar clip con timeline"}
            </Button>
            {submitInfo ? <p className="mt-2 text-xs text-neon-mint">{submitInfo}</p> : null}
            {submitError ? <p className="mt-2 text-xs text-rose-200">{submitError}</p> : null}
          </div> */}

          {videoEditarBool &&!isLoading && videos.length > 0 ? (
            <>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {videos.map((video) => {
                  return (
                    <button
                      type="button"
                      key={video.video_id}
                      onClick={() => {
                        setSelectedVideoId(video.video_id);
                        if (focusedClip && focusedClip.video_id !== video.video_id) {
                          setFocusedClip(null);
                        }
                      }}
                      className={[
                        "rounded-xl border px-3 py-2 text-left text-sm transition",
                        selectedVideoId === video.video_id
                          ? "border-neon-cyan/45 bg-neon-cyan/10 text-white"
                          : "border-white/10 bg-white/5 text-white/75 hover:border-white/20 hover:text-white"
                      ].join(" ")}
                    >
                      <p className="font-semibold">Video {video.video_id.slice(0, 8)}</p>
                      <p className="mt-1 text-xs text-white/60">Archivo: {video.filename}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.16em] text-neon-cyan/80">Estado: {video.status ?? "uploaded"}</p>
                    </button>
                  );
                })}
              </div>

              {totalPages > 1 ? (
                <div className="mt-4 flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/80">
                  <span>Pagina {page} de {totalPages}</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      className="rounded-lg border border-white/15 px-3 py-1.5 text-xs transition hover:border-white/35 disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={page <= 1 || isLoading}
                      onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                    >
                      Anterior
                    </button>
                    <button
                      type="button"
                      className="rounded-lg border border-white/15 px-3 py-1.5 text-xs transition hover:border-white/35 disabled:cursor-not-allowed disabled:opacity-40"
                      disabled={page >= totalPages || isLoading}
                      onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                    >
                      Siguiente
                    </button>
                  </div>
                </div>
              ) : null}
            </>
          ) : null}
        </Panel>

        <Panel>
          <p className="text-xs uppercase tracking-[0.22em] text-white/65">configuracion</p>
          <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Ajustes de recorte</h3>
          <VideoSettings submitInfoSettings={submitInfoSettings} submitErrorSettings={submitErrorSettings} videoEditarBool={videoEditarBool} draftFilename={draftFilename} setDraftFilename={setDraftFilename} saveRaname={saveRaname} trimStart={trimStart} trimEnd={trimEnd} minClipDurationSec={MIN_CLIP_SECONDS} isSubmitting={isSubmitting} submitInfo={submitInfo} selectedVideoId={selectedVideoId} submitError={submitError}  handleCreateJob={handleCreateJob} />
        </Panel>
      </div>
    </section>
  );
}
