import { Skeleton } from "@/src/components/ui/Skeleton";
import Link from "next/link";
import { useLocale } from "next-intl";

type Clip = {
  id: string;
  title: string;
  duration: string;
  preset: string;
  status: "listo" | "revision" | "render";
  previewUrl?: string | null;
  subtitlesUrl?: string | null;
};

type GeneratedClipsSectionProps = {
  clips: Clip[];
  showLoading: boolean;
  isRefreshingStatuses?: boolean;
  emptyMessage?: string;
};

const statusStyles: Record<Clip["status"], string> = {
  listo: "border-neon-mint/45 bg-neon-mint/15 text-neon-mint",
  revision: "border-neon-magenta/45 bg-neon-magenta/15 text-neon-magenta",
  render: "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
};

const MAX_ACTIVE_VIDEO_PREVIEWS = 6;

export function GeneratedClipsSection({
  clips,
  showLoading,
  isRefreshingStatuses = false,
  emptyMessage = "Todavia no hay clips generados. Subi un video para empezar."
}: GeneratedClipsSectionProps) {
  const isEn = useLocale() === "en";
  const tr = (es: string, en: string) => (isEn ? en : es);
  return (
    <section>
      <p className="text-xs uppercase tracking-[0.22em] text-white/65">{tr("clips generados", "generated clips")}</p>
      <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">{tr("Lista de resultados", "Results list")}</h3>

      {showLoading ? (
        <div className="mt-5 grid justify-center gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((id) => (
            <div key={id} className="w-full max-w-sm rounded-2xl border border-white/10 bg-night-900/45 p-4">
              <Skeleton className="aspect-[9/16] w-full rounded-xl" />
              <Skeleton className="mt-3 h-5 w-2/3" />
              <Skeleton className="mt-2 h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : clips.length === 0 ? (
        <div className="mt-5 rounded-2xl border border-white/10 bg-night-900/45 p-6 text-sm text-white/70">
          {isEn && emptyMessage === "Todavia no hay clips generados. Subi un video para empezar."
            ? "No clips generated yet. Upload a video to get started."
            : emptyMessage}
        </div>
      ) : (
        <div className="mt-5 grid justify-center gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {clips.map((clip, index) => (
            <article
              key={clip.id}
              className="w-full max-w-sm rounded-2xl border border-white/15 bg-gradient-to-b from-night-900/70 to-night-800/45 p-4 transition hover:-translate-y-0.5 hover:border-neon-cyan/35"
            >
              {clip.previewUrl && index < MAX_ACTIVE_VIDEO_PREVIEWS ? (
                <div className="overflow-hidden rounded-xl border border-neon-cyan/30 bg-black">
                  <video
                    controls
                    preload="metadata"
                    src={clip.previewUrl}
                    className="aspect-[9/16] w-full object-cover"
                  />
                </div>
              ) : clip.previewUrl ? (
                <div className="aspect-[9/16] rounded-xl border border-neon-cyan/30 bg-[radial-gradient(circle_at_30%_20%,rgba(53,208,255,0.24),transparent_45%),radial-gradient(circle_at_70%_80%,rgba(255,79,216,0.2),transparent_45%)] p-3">
                  <div className="flex h-full flex-col items-center justify-center gap-3 rounded-lg border border-white/15 bg-black/25 p-3 text-center text-xs text-white/75">
                    <p>{tr("Preview pausado para optimizar memoria del navegador.", "Preview paused to optimize browser memory.")}</p>
                    <a
                      href={clip.previewUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex rounded-lg border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-neon-cyan transition hover:bg-neon-cyan/20"
                    >
                      {tr("Abrir clip", "Open clip")}
                    </a>
                  </div>
                </div>
              ) : (
                <div className="aspect-[9/16] rounded-xl border border-neon-cyan/30 bg-[radial-gradient(circle_at_30%_20%,rgba(53,208,255,0.24),transparent_45%),radial-gradient(circle_at_70%_80%,rgba(255,79,216,0.2),transparent_45%)] p-3">
                  <div className="flex h-full items-center justify-center rounded-lg border border-white/15 bg-black/25 text-center text-xs text-white/75">
                    {clip.status === "listo" ? tr("Preparando preview...", "Preparing preview...") : tr("Procesando clip...", "Processing clip...")}
                  </div>
                </div>
              )}
              <div className="mt-3 flex items-center justify-between gap-2">
                <p className="font-display text-lg text-white">{clip.title}</p>
                <span
                  className={[
                    "rounded-lg border px-2 py-1 text-xs font-semibold uppercase",
                    statusStyles[clip.status]
                  ].join(" ")}
                >
                  {clip.status}
                </span>
              </div>
              <p className="mt-1 text-sm text-white/75">{clip.duration}</p>
              <p className="mt-2 rounded-lg border border-white/15 px-2 py-1 text-xs text-white/80">{tr("Preset", "Preset")}: {clip.preset}</p>
              {isRefreshingStatuses ? <p className="mt-2 text-xs text-white/60">{tr("Actualizando estado de jobs...", "Refreshing job statuses...")}</p> : null}
              <div className="mt-3 flex flex-wrap gap-2">
                <Link
                  href="/app/timeline"
                  className="inline-flex rounded-lg border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-neon-cyan transition hover:bg-neon-cyan/20"
                >
                  {tr("Editar en timeline", "Edit in timeline")}
                </Link>
                {clip.subtitlesUrl ? (
                  <a
                    href={clip.subtitlesUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex rounded-lg border border-neon-mint/35 bg-neon-mint/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-neon-mint transition hover:bg-neon-mint/20"
                  >
                    {tr("Ver subtitulos (.srt)", "View subtitles (.srt)")}
                  </a>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

export type { Clip };
