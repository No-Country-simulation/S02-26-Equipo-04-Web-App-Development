import { Loader } from "@/src/components/ui/Loader";
import { Button } from "@/src/components/ui/Button";
import { VideoSettingsModal } from "@/src/components/home/VideoSettingsModal";

type ProjectStatusPanelProps = {
  hasVideo: boolean;
  isUploading: boolean;
  uploadError: string | null;
  videoId: string | null;
  videoPreviewUrl: string | null;
  downloadUrl: string | null;
  isResolvingDownloadUrl: boolean;
  downloadError: string | null;
  onResolveDownloadUrl: () => Promise<void>;
};

export function ProjectStatusPanel({
  hasVideo,
  isUploading,
  uploadError,
  videoId,
  videoPreviewUrl,
  downloadUrl,
  isResolvingDownloadUrl,
  downloadError,
  onResolveDownloadUrl
}: ProjectStatusPanelProps) {
  const status = uploadError ? "Error de carga" : isUploading ? "Procesando" : hasVideo ? "Video cargado" : "Sin video";
  const progress = isUploading ? 45 : hasVideo ? 100 : 0;
  const showPreview = Boolean(videoPreviewUrl && hasVideo && !isUploading);

  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/80">estado del proyecto</p>
          <h3 className="mt-1 font-display text-2xl text-white">{status}</h3>
        </div>
        {/* <span className="rounded-lg border border-neon-violet/45 bg-neon-violet/15 px-3 py-1 text-xs font-semibold text-white">
          Mock
        </span> */}
      </div>

      {showPreview ? (
        <div className="mt-4 rounded-xl border border-white/15 bg-white/5 p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-white/80">Preview del video</span>
            <span className="text-neon-mint">Listo</span>
          </div>

          <div className="mt-2 overflow-hidden rounded-lg border border-white/15 bg-black/40">
            <video
              controls
              preload="metadata"
              className="max-h-44 w-full object-contain"
              src={videoPreviewUrl ?? undefined}
            />
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-xl border border-white/15 bg-white/5 p-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-white/80">Progreso</span>
            <span className="text-white">{progress}%</span>
          </div>
          <div className="mt-2 h-2 rounded-full bg-night-950/90">
            <div
              className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-violet transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <ul className="mt-4 space-y-2 text-sm text-white/80">
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Upload recibido</li>
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Analisis de escenas</li>
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Generacion de clips</li>
      </ul>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <VideoSettingsModal />
        <Button
          variant="neutral"
          className="h-10 w-auto px-4"
          onClick={() => {
            void onResolveDownloadUrl();
          }}
          disabled={!videoId || isResolvingDownloadUrl || isUploading}
        >
          {isResolvingDownloadUrl ? "Generando URL..." : "Obtener URL de descarga"}
        </Button>
      </div>

      {videoId ? <p className="mt-3 text-xs text-white/60">ID de video: {videoId}</p> : null}
      {uploadError ? (
        <p className="mt-3 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{uploadError}</p>
      ) : null}
      {downloadError ? (
        <p className="mt-3 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{downloadError}</p>
      ) : null}
      {downloadUrl ? (
        <a
          href={downloadUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex rounded-lg border border-neon-mint/40 bg-neon-mint/15 px-3 py-2 text-sm font-semibold text-neon-mint transition hover:bg-neon-mint/25"
        >
          Descargar video subido
        </a>
      ) : null}

      {isUploading ? <Loader className="mt-4" label="Analizando video en segundo plano..." /> : null}
    </section>
  );
}
