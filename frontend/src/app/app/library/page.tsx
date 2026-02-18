"use client";

import { Panel } from "@/src/components/ui/Panel";
import { Clock3, Download, Filter, Play, Search, Sparkles, Tag } from "lucide-react";

type ClipCard = {
  id: string;
  title: string;
  duration: string;
  source: string;
  preset: string;
  status: "listo" | "revision" | "render";
  ratio: "9:16" | "1:1";
};

const clips: ClipCard[] = [
  {
    id: "clip-01",
    title: "Hook de apertura",
    duration: "00:28",
    source: "entrevista-founder.mp4",
    preset: "Impact",
    status: "listo",
    ratio: "9:16"
  },
  {
    id: "clip-02",
    title: "Comparativa rapida",
    duration: "00:22",
    source: "demo-producto.mov",
    preset: "Fast Cut",
    status: "revision",
    ratio: "1:1"
  },
  {
    id: "clip-03",
    title: "CTA final",
    duration: "00:17",
    source: "webinar-growth.mp4",
    preset: "Story",
    status: "render",
    ratio: "9:16"
  },
  {
    id: "clip-04",
    title: "Momento viral",
    duration: "00:31",
    source: "podcast-episodio-12.mp4",
    preset: "Impact",
    status: "listo",
    ratio: "9:16"
  }
];

const statusStyles: Record<ClipCard["status"], string> = {
  listo: "border-emerald-300/40 bg-emerald-300/10 text-emerald-200",
  revision: "border-amber-300/45 bg-amber-300/10 text-amber-100",
  render: "border-sky-300/45 bg-sky-300/10 text-sky-100"
};

export default function LibraryPage() {
  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <Panel className="relative overflow-hidden border-neon-cyan/25 bg-gradient-to-r from-night-900 via-night-800/85 to-night-900 p-5 sm:p-6">
        <div className="pointer-events-none absolute -right-14 -top-14 h-52 w-52 rounded-full bg-neon-cyan/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 left-1/4 h-44 w-44 rounded-full bg-neon-magenta/15 blur-3xl" />

        <div className="relative animate-fade-up">
          <p className="text-xs uppercase tracking-[0.25em] text-neon-cyan/80">biblioteca clips</p>
          <h1 className="mt-2 font-display text-2xl text-white sm:text-3xl">Todos tus clips en un solo lugar</h1>
          <p className="mt-2 max-w-2xl text-sm text-white/70">
            Visualiza resultados, revisa estado de render y organiza salidas para publicar mas rapido.
          </p>
        </div>

        <div className="relative mt-5 grid gap-3 sm:grid-cols-[1fr_auto_auto]">
          <label className="group flex items-center gap-3 rounded-xl border border-white/12 bg-white/5 px-3 py-2 transition hover:border-neon-cyan/40">
            <Search size={15} className="text-neon-cyan/80" />
            <input
              placeholder="Buscar por titulo o archivo..."
              className="w-full bg-transparent text-sm text-white/90 outline-none placeholder:text-white/40"
            />
          </label>

          <button className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/80 transition hover:border-neon-cyan/45 hover:text-white">
            <Filter size={14} />
            Filtros
          </button>

          <button className="inline-flex items-center justify-center gap-2 rounded-xl border border-neon-cyan/45 bg-neon-cyan/10 px-4 py-2 text-sm text-neon-cyan transition hover:bg-neon-cyan/20">
            <Sparkles size={14} />
            Nueva seleccion IA
          </button>
        </div>
      </Panel>

      <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {clips.map((clip, index) => (
          <article
            key={clip.id}
            className="group animate-fade-up rounded-2xl border border-white/10 bg-gradient-to-b from-night-800/80 to-night-900/80 p-4 shadow-panel transition duration-300 hover:-translate-y-1 hover:border-neon-cyan/40"
            style={{ animationDelay: `${index * 90}ms` }}
          >
            <div className="relative mb-3 overflow-hidden rounded-xl border border-white/10 bg-night-900/80">
              <div className="aspect-[9/13] bg-[radial-gradient(circle_at_20%_20%,rgba(53,208,255,0.32),transparent_45%),radial-gradient(circle_at_80%_78%,rgba(255,79,216,0.28),transparent_50%),#0d1630]" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-transparent to-transparent" />

              <button className="absolute left-3 top-3 grid h-8 w-8 place-items-center rounded-full border border-white/30 bg-night-900/70 text-white transition group-hover:animate-drift group-hover:border-neon-cyan/70 group-hover:text-neon-cyan">
                <Play size={14} />
              </button>

              <span className={`absolute right-3 top-3 rounded-full border px-2 py-1 text-[10px] uppercase tracking-[0.2em] ${statusStyles[clip.status]}`}>
                {clip.status}
              </span>

              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs text-white/85">
                <span className="inline-flex items-center gap-1 rounded-full bg-black/35 px-2 py-1 backdrop-blur-sm">
                  <Clock3 size={12} />
                  {clip.duration}
                </span>
                <span className="rounded-full bg-black/35 px-2 py-1 backdrop-blur-sm">{clip.ratio}</span>
              </div>
            </div>

            <h2 className="font-display text-lg text-white">{clip.title}</h2>

            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1 rounded-full border border-neon-violet/35 bg-neon-violet/10 px-2 py-1 text-neon-violet">
                <Tag size={11} />
                {clip.preset}
              </span>
              <span className="rounded-full border border-white/15 bg-white/5 px-2 py-1 text-white/70">{clip.source}</span>
            </div>

            <div className="mt-4 flex items-center gap-2">
              <button className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-neon-cyan/40 bg-neon-cyan/10 px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-neon-cyan transition hover:bg-neon-cyan/20">
                <Download size={13} />
                Descargar
              </button>
              <button className="rounded-lg border border-white/15 bg-white/5 px-3 py-2 text-xs text-white/80 transition hover:border-white/30 hover:text-white">
                Ver detalles
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
