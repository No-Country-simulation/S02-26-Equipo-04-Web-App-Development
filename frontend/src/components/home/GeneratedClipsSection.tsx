import { Skeleton } from "@/src/components/ui/Skeleton";
import { ReponseReframeGetJob } from "@/src/services/videoApi";
import Link from "next/link";

type Clip = {
  id: string;
  title: string;
  duration: string;
  preset: string;
  status: "listo" | "revision" | "render";
};

type GeneratedClipsSectionProps = {
  video:ReponseReframeGetJob | null
  clips: Clip[];
  showLoading: boolean;
};

const statusStyles: Record<Clip["status"], string> = {
  listo: "border-neon-mint/45 bg-neon-mint/15 text-neon-mint",
  revision: "border-neon-magenta/45 bg-neon-magenta/15 text-neon-magenta",
  render: "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
};
export function GeneratedClipsSection({video, clips, showLoading }: GeneratedClipsSectionProps) {
  console.log(video?.output_path)

  return (
    <section>
      <p className="text-xs uppercase tracking-[0.22em] text-white/65">clips generados</p>
      <h3 className="mt-1 font-display text-2xl text-white sm:text-3xl">Lista de resultados</h3>

      {showLoading ? (
        <div className="mt-5 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(14rem,1fr))]">
          {[1, 2, 3].map((id) => (
            <div key={id} className="rounded-2xl border border-white/10 bg-night-900/45 p-4">
              <Skeleton className="aspect-[9/16] w-full rounded-xl" />
              <Skeleton className="mt-3 h-5 w-2/3" />
              <Skeleton className="mt-2 h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : clips.length === 0 ? (
        <div className="mt-5 rounded-2xl border border-white/10 bg-night-900/45 p-6 text-sm text-white/70">
          Todavia no hay clips generados. Subi un video para empezar.
        </div>
      ) : (
        <Link href={`/app/shortDetails/${video?.job_id}`} className="mt-5 grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(14rem,1fr))]">
          {clips.map((clip) => (
            <article
              key={clip.id}
              className="rounded-2xl border border-white/15 bg-gradient-to-b from-night-900/70 to-night-800/45 p-4 transition hover:-translate-y-0.5 hover:border-neon-cyan/35"
            >
           
              <div className="aspect-[9/16] rounded-xl border border-neon-cyan/30 bg-[radial-gradient(circle_at_30%_20%,rgba(53,208,255,0.24),transparent_45%),radial-gradient(circle_at_70%_80%,rgba(255,79,216,0.2),transparent_45%)]" />
                            {/* <video controls src={video?.output_path}/> */}

              <div className="mt-3 flex items-center justify-between gap-2">
                
                <p className="font-display text-lg text-white">Titulo</p>
                <span
                  className={[
                    "rounded-lg border px-2 py-1 text-xs font-semibold uppercase",
                    // statusStyles[clip.status]
                  ].join(" ")}
                >
                  {/* {clip.status} */}
                </span>
              </div>
              <p className="mt-1 text-sm text-white/75">Duracion</p>
              {/* <p className="mt-2 rounded-lg border border-white/15 px-2 py-1 text-xs text-white/80">Preset: {clip.preset}</p> */}
            </article>
          ))}
        </Link>
      )}
    </section>
  );
}

export type { Clip };
