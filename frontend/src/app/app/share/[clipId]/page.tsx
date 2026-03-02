"use client";

import { Button } from "@/src/components/ui/Button";
import { Panel } from "@/src/components/ui/Panel";
import { authApi } from "@/src/services/authApi";
import { videoApi, type UserClipItem, type YoutubeConnectionStatus, VideoApiError } from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Facebook, Instagram, MessageCircle, Music2, Share2, Youtube } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { type ComponentType, useEffect, useState } from "react";

type SocialTarget = {
  id: "instagram" | "tiktok" | "facebook" | "youtube" | "x" | "whatsapp";
  label: string;
  icon: ComponentType<{ size?: number; className?: string }>;
};

const socialTargets: SocialTarget[] = [
  { id: "instagram", label: "Instagram", icon: Instagram },
  { id: "tiktok", label: "TikTok", icon: Music2 },
  { id: "facebook", label: "Facebook", icon: Facebook },
  { id: "youtube", label: "YouTube", icon: Youtube },
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
  const [youtubeStatus, setYoutubeStatus] = useState<YoutubeConnectionStatus | null>(null);
  const [isLoadingYoutubeStatus, setIsLoadingYoutubeStatus] = useState(false);
  const [isPublishingYoutube, setIsPublishingYoutube] = useState(false);
  const [youtubeTitle, setYoutubeTitle] = useState("");
  const [youtubeDescription, setYoutubeDescription] = useState("");
  const [youtubePrivacy, setYoutubePrivacy] = useState<"public" | "private" | "unlisted">("private");
  const canPublishClip = clip ? ["done", "completed"].includes(clip.status.toLowerCase()) : false;

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

    const loadYoutubeStatus = async () => {
      setIsLoadingYoutubeStatus(true);
      try {
        const response = await videoApi.getYoutubeStatus(token);
        if (!cancelled) {
          setYoutubeStatus(response);
        }
      } catch {
        if (!cancelled) {
          setYoutubeStatus(null);
        }
      } finally {
        if (!cancelled) {
          setIsLoadingYoutubeStatus(false);
        }
      }
    };

    void loadClip();
    void loadYoutubeStatus();

    return () => {
      cancelled = true;
    };
  }, [clipId, token]);

  useEffect(() => {
    if (!clip) {
      return;
    }

    setYoutubeTitle(`Clip ${clip.job_id.slice(0, 8)} - Hacelo Corto`);
    setYoutubeDescription(`Clip generado desde ${clip.source_filename}`);
  }, [clip]);

  const handleConnectYoutube = async () => {
    setInfo(null);
    try {
      const oauth = await authApi.getGoogleAuthUrl();
      window.sessionStorage.setItem("google_oauth_state", oauth.state);
      window.location.href = oauth.authorization_url;
    } catch {
      setError("No pudimos iniciar la conexion con YouTube via Google OAuth.");
    }
  };

  const handlePublishYoutube = async () => {
    if (!token || !clip) {
      setError("No hay sesion activa o clip seleccionado para publicar.");
      return;
    }

    setIsPublishingYoutube(true);
    setError(null);
    setInfo(null);

    try {
      const response = await videoApi.publishToYoutube(clip.job_id, token, {
        title: youtubeTitle.trim() || undefined,
        description: youtubeDescription.trim() || undefined,
        privacy: youtubePrivacy
      });

      setInfo(`Publicado en YouTube: ${response.youtube_url}`);
    } catch (publishError) {
      setError(normalizeVideoError(publishError, "No pudimos publicar el clip en YouTube."));
    } finally {
      setIsPublishingYoutube(false);
    }
  };

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <Panel className="relative overflow-hidden border-neon-mint/25 bg-gradient-to-r from-night-900 via-night-800/80 to-night-900 p-5 sm:p-6">
        <div className="pointer-events-none absolute -right-14 -top-20 h-52 w-52 animate-drift rounded-full bg-neon-cyan/12 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -left-10 h-52 w-52 animate-drift rounded-full bg-neon-violet/12 blur-3xl [animation-delay:400ms]" />

        <div className="relative animate-fade-up">
          <p className="text-xs uppercase tracking-[0.25em] text-neon-mint/75">compartir clip</p>
          <h1 className="mt-2 font-display text-2xl text-white sm:text-3xl">Publicacion por red social</h1>
          <p className="mt-2 text-sm text-white/70">
            Desde esta pantalla podras conectar la subida individual de un clip para cada red. Por ahora dejamos el flujo preparado.
          </p>
        </div>

        {isLoading ? <p className="mt-4 text-sm text-white/70">Cargando clip...</p> : null}

        {error ? (
          <p className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">{error}</p>
        ) : null}

        {!isLoading && !error && clip ? (
          <div className="mt-5 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="animate-fade-up rounded-2xl border border-white/10 bg-night-900/70 p-4 [animation-delay:90ms]">
              {clip.output_path ? (
                <video
                  controls
                  preload="metadata"
                  className="mx-auto aspect-[9/13] w-full max-w-[320px] rounded-xl border border-white/10 object-cover sm:max-w-[380px] lg:max-w-none"
                  src={clip.output_path}
                />
              ) : (
                <div className="mx-auto grid aspect-[9/13] w-full max-w-[320px] place-items-center rounded-xl border border-white/10 bg-night-800/80 text-sm text-white/65 sm:max-w-[380px] lg:max-w-none">
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
              {socialTargets.map((target, index) => {
                const Icon = target.icon;
                const isYoutube = target.id === "youtube";
                const isYoutubeConnected = Boolean(youtubeStatus?.connected);
                return (
                  <div
                    key={target.id}
                    className="animate-fade-up rounded-xl border border-white/12 bg-white/5 p-3 transition duration-300 hover:border-neon-cyan/30 hover:bg-white/7"
                    style={{ animationDelay: `${160 + index * 60}ms` }}
                  >
                    <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-center">
                      <div>
                        <p className="inline-flex items-center gap-2 text-sm font-semibold text-white">
                          <Icon size={16} className="text-neon-mint" />
                          {target.label}
                        </p>
                        <p className="mt-1 text-xs text-white/65">
                          {isYoutube
                            ? isLoadingYoutubeStatus
                              ? "Validando conexion con YouTube..."
                              : isYoutubeConnected
                                ? `Cuenta vinculada${youtubeStatus?.provider_username ? ` (${youtubeStatus.provider_username})` : ""}`
                                : "Cuenta pendiente de vincular"
                            : "Integracion en roadmap. Disponible proximamente."}
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-2 sm:min-w-[260px]">
                        <Button
                          className="h-9 px-3 py-2 text-xs"
                          variant={isYoutubeConnected ? "neutral" : "violet"}
                          disabled={!isYoutube || isLoadingYoutubeStatus}
                          onClick={isYoutube ? () => void handleConnectYoutube() : undefined}
                        >
                          {isYoutubeConnected ? "Reconectar" : "Conectar"}
                        </Button>
                        <Button
                          className="h-9 px-3 py-2 text-xs"
                          disabled={!isYoutube || !isYoutubeConnected || isPublishingYoutube || !canPublishClip}
                          onClick={isYoutube ? () => void handlePublishYoutube() : undefined}
                        >
                          {isPublishingYoutube ? "Publicando..." : "Publicar clip"}
                        </Button>
                      </div>
                    </div>

                    {isYoutube && !canPublishClip ? (
                      <p className="mt-2 text-xs text-amber-200">Este clip debe estar en estado DONE para poder publicarse en YouTube.</p>
                    ) : null}

                    {isYoutube ? (
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        <label className="text-xs text-white/75 sm:col-span-2">
                          Titulo
                          <input
                            value={youtubeTitle}
                            onChange={(event) => setYoutubeTitle(event.target.value.slice(0, 100))}
                            maxLength={100}
                            className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50"
                          />
                        </label>
                        <label className="text-xs text-white/75 sm:col-span-2">
                          Descripcion
                          <textarea
                            value={youtubeDescription}
                            onChange={(event) => setYoutubeDescription(event.target.value.slice(0, 5000))}
                            maxLength={5000}
                            rows={3}
                            className="mt-1 w-full resize-y rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50"
                          />
                        </label>
                        <label className="text-xs text-white/75 sm:col-span-2">
                          Privacidad
                          <select
                            value={youtubePrivacy}
                            onChange={(event) => setYoutubePrivacy(event.target.value as "public" | "private" | "unlisted")}
                            className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50"
                          >
                            <option value="private">private</option>
                            <option value="unlisted">unlisted</option>
                            <option value="public">public</option>
                          </select>
                        </label>
                      </div>
                    ) : null}
                  </div>
                );
              })}

              {info ? (
                <p className="animate-fade-up rounded-xl border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-2 text-xs text-neon-cyan [animation-delay:260ms]">
                  {info}
                </p>
              ) : null}
              <Link
                href="/app/library"
                className="animate-fade-up inline-flex items-center gap-2 rounded-lg border border-white/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-white/80 transition hover:border-white/40 hover:text-white [animation-delay:320ms]"
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
