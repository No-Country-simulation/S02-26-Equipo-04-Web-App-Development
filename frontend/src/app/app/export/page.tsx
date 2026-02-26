"use client";

import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserClipItem } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Check, Clock3, Copy, Download, FolderOpen, Link2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const PAGE_SIZE = 30;

function formatDateLabel(raw: string) {
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) {
    return "fecha desconocida";
  }
  return new Intl.DateTimeFormat("es-AR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function isClipReady(status: string) {
  const normalized = status.toLowerCase();
  return normalized === "done" || normalized === "completed";
}

export default function ExportPage() {
  const token = useAuthStore((state) => state.token);
  const [clips, setClips] = useState<UserClipItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setError("No encontramos sesion activa para cargar exportaciones.");
      return;
    }

    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await videoApi.getMyClips(token, { limit: PAGE_SIZE, offset: 0 });
        if (cancelled) {
          return;
        }
        setClips(response.clips);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "No pudimos cargar tus clips para exportacion.");
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const readyClips = useMemo(
    () => clips.filter((clip) => isClipReady(clip.status) && Boolean(clip.output_path)),
    [clips]
  );
  const pendingClips = useMemo(() => clips.filter((clip) => !isClipReady(clip.status)), [clips]);

  const handleCopyLink = async (clip: UserClipItem) => {
    if (!clip.output_path) {
      return;
    }

    try {
      await navigator.clipboard.writeText(clip.output_path);
      setCopiedId(clip.job_id);
      window.setTimeout(() => setCopiedId((prev) => (prev === clip.job_id ? null : prev)), 1800);
    } catch {
      setError("No pudimos copiar el enlace al portapapeles.");
    }
  };

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <Panel className="relative overflow-hidden border-neon-cyan/25 bg-gradient-to-r from-night-900 via-night-800/90 to-night-900 p-5 sm:p-6">
        <div className="pointer-events-none absolute -right-14 -top-16 h-56 w-56 rounded-full bg-neon-cyan/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 left-1/4 h-44 w-44 rounded-full bg-neon-mint/10 blur-3xl" />

        <div className="relative animate-fade-up">
          <p className="text-xs uppercase tracking-[0.25em] text-neon-cyan/80">exportacion</p>
          <h1 className="mt-2 font-display text-2xl text-white sm:text-3xl">Centro de exportacion de clips</h1>
          <p className="mt-2 max-w-2xl text-sm text-white/70">
            Descarga tus ultimos clips listos, copia enlaces para compartir y controla rapidamente que piezas todavia siguen en proceso.
          </p>
        </div>

        <div className="relative mt-5 grid gap-3 sm:grid-cols-3">
          <div className="rounded-xl border border-neon-cyan/30 bg-neon-cyan/10 p-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-neon-cyan/85">Clips listos</p>
            <p className="mt-1 font-display text-2xl text-white">{readyClips.length}</p>
          </div>
          <div className="rounded-xl border border-amber-300/30 bg-amber-300/10 p-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-amber-100/85">En proceso</p>
            <p className="mt-1 font-display text-2xl text-white">{pendingClips.length}</p>
          </div>
          <div className="rounded-xl border border-white/15 bg-white/5 p-3">
            <p className="text-[11px] uppercase tracking-[0.18em] text-white/65">Total reciente</p>
            <p className="mt-1 font-display text-2xl text-white">{clips.length}</p>
          </div>
        </div>
      </Panel>

      {error ? (
        <Panel className="mt-5">
          <p className="rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>
        </Panel>
      ) : null}

      {isLoading ? (
        <Panel className="mt-5">
          <p className="text-sm text-white/70">Preparando exportaciones...</p>
        </Panel>
      ) : null}

      {!isLoading && readyClips.length === 0 ? (
        <Panel className="mt-5">
          <p className="text-sm text-white/70">Todavia no hay clips listos para exportar.</p>
        </Panel>
      ) : null}

      {readyClips.length > 0 ? (
        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {readyClips.map((clip, index) => (
            <article
              key={clip.job_id}
              className="group animate-fade-up rounded-2xl border border-white/10 bg-gradient-to-b from-night-800/80 to-night-900/80 p-4 shadow-panel transition duration-300 hover:-translate-y-1 hover:border-neon-cyan/40"
              style={{ animationDelay: `${index * 70}ms` }}
            >
              <div className="relative mb-3 overflow-hidden rounded-xl border border-white/10 bg-night-900/80">
                {clip.output_path ? (
                  <video controls preload="metadata" className="aspect-[9/13] w-full object-cover" src={clip.output_path} />
                ) : (
                  <div className="aspect-[9/13] bg-night-900" />
                )}
                <span className="absolute right-3 top-3 rounded-full border border-emerald-300/40 bg-emerald-300/15 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-emerald-200">
                  listo
                </span>
              </div>

              <h2 className="font-display text-lg text-white">Clip {clip.job_id.slice(0, 8)}</h2>
              <p className="mt-1 text-xs text-white/65">{clip.source_filename}</p>
              <p className="mt-2 inline-flex items-center gap-1 rounded-full border border-white/15 bg-white/5 px-2 py-1 text-[11px] text-white/70">
                <Clock3 size={12} /> {formatDateLabel(clip.created_at)}
              </p>

              <div className="mt-4 grid grid-cols-2 gap-2">
                <a
                  href={clip.output_path ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center justify-center gap-1 rounded-lg border border-neon-cyan/40 bg-neon-cyan/10 px-2 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-neon-cyan transition hover:bg-neon-cyan/20"
                >
                  <Download size={12} /> Descargar
                </a>
                <button
                  type="button"
                  onClick={() => void handleCopyLink(clip)}
                  className="inline-flex items-center justify-center gap-1 rounded-lg border border-neon-mint/40 bg-neon-mint/10 px-2 py-2 text-[11px] font-semibold uppercase tracking-[0.12em] text-neon-mint transition hover:bg-neon-mint/20"
                >
                  {copiedId === clip.job_id ? <Check size={12} /> : <Copy size={12} />}
                  {copiedId === clip.job_id ? "Copiado" : "Copiar link"}
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {pendingClips.length > 0 ? (
        <Panel className="mt-5 border-white/12 bg-white/5 p-4 sm:p-5">
          <div className="flex items-center gap-2 text-white/85">
            <FolderOpen size={15} className="text-neon-cyan" />
            <p className="text-sm font-medium">Clips en proceso</p>
          </div>

          <div className="mt-3 space-y-2">
            {pendingClips.slice(0, 6).map((clip) => (
              <div
                key={clip.job_id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/10 bg-night-900/45 px-3 py-2 text-xs"
              >
                <span className="text-white/70">{clip.source_filename}</span>
                <span className="inline-flex items-center gap-1 rounded-full border border-amber-300/40 bg-amber-300/10 px-2 py-1 uppercase tracking-[0.14em] text-amber-100">
                  <Link2 size={11} /> {clip.status}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      ) : null}
    </section>
  );
}
