import { Loader } from "@/src/components/ui/Loader";
// import { VideoSettingsModal } from "@/src/components/home/VideoSettingsModal";

type ProjectStatusPanelProps = {
  hasVideo: boolean;
  hasAudio: boolean;
  isUploading: boolean;
  uploadError: string | null;
  isCreatingJobs: boolean;
  jobsCreated: number;
  clipsPending: number;
  clipProgressPercent: number;
  jobError: string | null;
};

export function ProjectStatusPanel({
  hasVideo,
  hasAudio,
  isUploading,
  uploadError,
  isCreatingJobs,
  jobsCreated,
  clipsPending,
  clipProgressPercent,
  jobError
}: ProjectStatusPanelProps) {
  let status = "Sin video";
  if (uploadError) {
    status = "Error de carga";
  } else if (jobError) {
    status = "Error al crear clips";
  } else if (isUploading) {
    status = "Subiendo archivo";
  } else if (isCreatingJobs) {
    status = "Creando clips";
  } else if (jobsCreated > 0 && clipsPending > 0) {
    status = "Clips en proceso";
  } else if (jobsCreated > 0) {
    status = "Clips listos";
  } else if (hasAudio) {
    status = "Audio cargado";
  } else if (hasVideo) {
    status = "Video cargado";
  }

  const uploadProgress = isUploading ? 60 : hasVideo || hasAudio ? 100 : 0;
  const generationProgress = isCreatingJobs
    ? 25
    : jobsCreated > 0
      ? clipProgressPercent
      : hasVideo
        ? 10
        : 0;

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
          <span className="text-white/80">Subida de archivo</span>
          <span className="text-white">{uploadProgress}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-night-950/90">
          <div
            className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-mint transition-all duration-500"
            style={{ width: `${uploadProgress}%` }}
          />
        </div>

        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-white/80">Generacion de clips</span>
          <span className="text-white">{generationProgress}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-night-950/90">
          <div
            className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-violet transition-all duration-500"
            style={{ width: `${generationProgress}%` }}
          />
        </div>
      </div>

      {uploadError ? (
        <p className="mt-3 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{uploadError}</p>
      ) : null}
      {jobError ? (
        <p className="mt-3 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{jobError}</p>
      ) : null}

      {isUploading || isCreatingJobs ? (
        <Loader className="mt-4" label={isUploading ? "Subiendo archivo..." : "Creando clips automaticos..."} />
      ) : null}
    </section>
  );
}
