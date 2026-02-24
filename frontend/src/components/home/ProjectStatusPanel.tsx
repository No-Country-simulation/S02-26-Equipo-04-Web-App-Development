import { Loader } from "@/src/components/ui/Loader";
// import { VideoSettingsModal } from "@/src/components/home/VideoSettingsModal";

type ProjectStatusPanelProps = {
  hasVideo: boolean;
  isUploading: boolean;
  uploadError: string | null;
  videoId: string | null;
  isCreatingJobs: boolean;
  jobsCreated: number;
  jobError: string | null;
};

export function ProjectStatusPanel({
  hasVideo,
  isUploading,
  uploadError,
  videoId,
  isCreatingJobs,
  jobsCreated,
  jobError
}: ProjectStatusPanelProps) {
  const status = uploadError
    ? "Error de carga"
    : jobError
      ? "Error al crear clips"
      : isUploading
        ? "Subiendo video"
        : isCreatingJobs
          ? "Creando clips"
          : jobsCreated > 0
            ? "Clips en proceso"
            : hasVideo
              ? "Video cargado"
              : "Sin video";

  const progress = isUploading ? 35 : isCreatingJobs ? 70 : jobsCreated > 0 ? 100 : hasVideo ? 55 : 0;

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

      <ul className="mt-4 space-y-2 text-sm text-white/80">
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Upload recibido</li>
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Generacion automatica de segmentos</li>
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Encolado de jobs de reframe</li>
      </ul>
      {jobsCreated > 0 ? <p className="mt-3 text-xs text-neon-cyan">Jobs creados: {jobsCreated}</p> : null}
      {videoId ? <p className="mt-3 text-xs text-white/60">ID de video: {videoId}</p> : null}
      {uploadError ? (
        <p className="mt-3 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{uploadError}</p>
      ) : null}
      {jobError ? (
        <p className="mt-3 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{jobError}</p>
      ) : null}

      {isUploading || isCreatingJobs ? (
        <Loader className="mt-4" label={isUploading ? "Subiendo video..." : "Creando clips automaticos..."} />
      ) : null}
    </section>
  );
}
