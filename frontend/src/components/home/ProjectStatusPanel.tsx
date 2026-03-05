import { Loader } from "@/src/components/ui/Loader";
import { useLocale } from "next-intl";
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
  const isEn = useLocale() === "en";
  const tr = (es: string, en: string) => (isEn ? en : es);
  let status = "Sin video";
  if (uploadError) {
    status = tr("Error de carga", "Upload error");
  } else if (jobError) {
    status = tr("Error al crear clips", "Clip generation error");
  } else if (isUploading) {
    status = tr("Subiendo archivo", "Uploading file");
  } else if (isCreatingJobs) {
    status = tr("Creando clips", "Creating clips");
  } else if (jobsCreated > 0 && clipsPending > 0) {
    status = tr("Clips en proceso", "Clips in progress");
  } else if (jobsCreated > 0) {
    status = tr("Clips listos", "Clips ready");
  } else if (hasAudio) {
    status = tr("Audio cargado", "Audio uploaded");
  } else if (hasVideo) {
    status = tr("Video cargado", "Video uploaded");
  } else {
    status = tr("Sin video", "No video");
  }

  const uploadProgress = isUploading ? 60 : hasVideo || hasAudio ? 100 : 0;
  const generationProgress = isCreatingJobs
    ? 25
    : jobsCreated > 0
      ? clipProgressPercent
      : hasVideo
        ? 10
        : 0;
  const generationCountLabel =
    jobsCreated > 0 ? `${clipsPending}/${jobsCreated} ${tr("en proceso", "in progress")}` : isCreatingJobs ? tr("Calculando cantidad...", "Calculating amount...") : "";

  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/80">{tr("estado del proyecto", "project status")}</p>
          <h3 className="mt-1 font-display text-2xl text-white">{status}</h3>
        </div>
        {/* <span className="rounded-lg border border-neon-violet/45 bg-neon-violet/15 px-3 py-1 text-xs font-semibold text-white">
          Mock
        </span> */}
      </div>

      <div className="mt-4 rounded-xl border border-white/15 bg-white/5 p-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/80">{tr("Subida de archivo", "File upload")}</span>
          <span className="text-white">{uploadProgress}%</span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-night-950/90">
          <div
            className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-mint transition-all duration-500"
            style={{ width: `${uploadProgress}%` }}
          />
        </div>

        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-white/80">{tr("Generacion de clips", "Clip generation")}</span>
          <div className="text-right">
            <p className="text-white">{generationProgress}%</p>
            {generationCountLabel ? <p className="text-[11px] text-white/60">{generationCountLabel}</p> : null}
          </div>
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
        <Loader className="mt-4" label={isUploading ? tr("Subiendo archivo...", "Uploading file...") : tr("Creando clips automaticos...", "Creating automatic clips...")} />
      ) : null}
    </section>
  );
}
