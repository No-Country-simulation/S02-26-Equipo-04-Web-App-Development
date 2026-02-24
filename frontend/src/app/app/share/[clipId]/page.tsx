"use client";

import { Button } from "@/src/components/ui/Button";
import { Panel } from "@/src/components/ui/Panel";
import { videoApi, type UserClipItem, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Facebook, Instagram, MessageCircle, Music2, Share2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { type ComponentType, useEffect, useState } from "react";

type SocialTarget = {
  id: string;
  label: string;
  icon: ComponentType<{ size?: number; className?: string }>;
};

const socialTargets: SocialTarget[] = [
  { id: "instagram", label: "Instagram", icon: Instagram },
  { id: "tiktok", label: "TikTok", icon: Music2 },
  { id: "facebook", label: "Facebook", icon: Facebook },
  { id: "x", label: "X", icon: Share2 },
  { id: "whatsapp", label: "WhatsApp", icon: MessageCircle }
];

function normalizeVideoError(error: unknown, fallbackMessage: string) {
  if (error instanceof VideoApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallbackMessage;
}

export default function ShareClipPage() {
  const params = useParams<{ clipId: string }>();
  const clipId = params?.clipId ?? "";
  const token = useAuthStore((state) => state.token);

  const [clip, setClip] = useState<UserClipItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setError("No encontramos una sesion activa para compartir este clip.");
      return;
    }

    let cancelled = false;

    const loadClip = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await videoApi.getMyClips(token, {
          limit: 10,
          offset: 0,
          query: clipId
        });

        const selectedClip = response.clips.find((item) => item.job_id === clipId) ?? null;

        if (!cancelled) {
          if (!selectedClip) {
            setError("No encontramos el clip solicitado.");
            setClip(null);
          } else {
            setClip(selectedClip);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(normalizeVideoError(loadError, "No pudimos cargar el clip para compartir."));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadClip();

    return () => {
      cancelled = true;
    };
  }, [clipId, token]);

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <Panel className="border-neon-mint/25 bg-gradient-to-r from-night-900 via-night-800/80 to-night-900 p-5 sm:p-6">
        <p className="text-xs uppercase tracking-[0.25em] text-neon-mint/75">compartir clip</p>
        <h1 className="mt-2 font-display text-2xl text-white sm:text-3xl">Publicacion por red social</h1>
        <p className="mt-2 text-sm text-white/70">
          Desde esta pantalla podras conectar la subida individual de un clip para cada red. Por ahora dejamos el flujo preparado.
        </p>

        {isLoading ? <p className="mt-4 text-sm text-white/70">Cargando clip...</p> : null}

        {error ? (
          <p className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>
        ) : null}

        {!isLoading && !error && clip ? (
          <div className="mt-5 grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="rounded-2xl border border-white/10 bg-night-900/70 p-4">
              {clip.output_path ? (
                <video controls preload="metadata" className="aspect-[9/13] w-full rounded-xl border border-white/10 object-cover" src={clip.output_path} />
              ) : (
                <div className="grid aspect-[9/13] place-items-center rounded-xl border border-white/10 bg-night-800/80 text-sm text-white/65">
                  El clip todavia no tiene preview disponible.
                </div>
              )}

              <div className="mt-3 space-y-1 text-xs text-white/75">
                <p>Clip: {clip.job_id}</p>
                <p>Video: {clip.video_id}</p>
                <p>Estado: {clip.status}</p>
              </div>
            </div>

            <div className="space-y-3">
              {socialTargets.map((target) => {
                const Icon = target.icon;
                return (
                  <div key={target.id} className="rounded-xl border border-white/12 bg-white/5 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="inline-flex items-center gap-2 text-sm font-semibold text-white">
                        <Icon size={16} className="text-neon-mint" />
                        {target.label}
                      </p>
                      <Button
                        className="w-auto px-3 py-2 text-xs"
                        onClick={() => setInfo(`Flujo de subida a ${target.label} preparado. Integramos API en el siguiente paso.`)}
                      >
                        Subir
                      </Button>
                    </div>
                  </div>
                );
              })}

              {info ? <p className="rounded-xl border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-2 text-xs text-neon-cyan">{info}</p> : null}
              <Link
                href="/app/library"
                className="inline-flex items-center gap-2 rounded-lg border border-white/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-white/80 transition hover:border-white/40 hover:text-white"
              >
                Volver a biblioteca
              </Link>
            </div>
          </div>
        ) : null}
      </Panel>
    </section>
  );
}
