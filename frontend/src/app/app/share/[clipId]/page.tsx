"use client";

import { Button } from "@/src/components/ui/Button";
import { Panel } from "@/src/components/ui/Panel";
import { authApi } from "@/src/services/authApi";
import {
  videoApi,
  type UserClipItem,
  type YoutubeConnectionStatus,
  type YoutubeMetadataSuggestionTone,
  VideoApiError
} from "@/src/services/videoApi";
import { useAuthStore } from "@/src/store/useAuthStore";
import { AlertTriangle, CheckCircle2, Facebook, Instagram, MessageCircle, Music2, Share2, Sparkles, Youtube } from "lucide-react";
import Link from "next/link";
import { useLocale } from "next-intl";
import { useParams } from "next/navigation";
import { type ComponentType, useCallback, useEffect, useMemo, useState } from "react";

type SocialTarget = {
  id: "instagram" | "tiktok" | "facebook" | "youtube" | "x" | "whatsapp";
  label: string;
  icon: ComponentType<{ size?: number; className?: string }>;
};

type ShareYoutubeDraft = {
  title: string;
  description: string;
  privacy: "public" | "private" | "unlisted";
  tone: YoutubeMetadataSuggestionTone;
  hashtags: string[];
  tags: string[];
  provider: string | null;
};

const socialTargets: SocialTarget[] = [
  { id: "instagram", label: "Instagram", icon: Instagram },
  { id: "tiktok", label: "TikTok", icon: Music2 },
  { id: "facebook", label: "Facebook", icon: Facebook },
  { id: "youtube", label: "YouTube", icon: Youtube },
  { id: "x", label: "X", icon: Share2 },
  { id: "whatsapp", label: "WhatsApp", icon: MessageCircle }
];

const shareDraftPrefix = "share:youtube-metadata";

function getShareDraftKey(clipId: string, locale: string) {
  return `${shareDraftPrefix}:${clipId}:${locale}`;
}

function normalizeVideoError(error: unknown, fallbackMessage: string, isEn: boolean) {
  if (error instanceof VideoApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    const normalized = error.message.toLowerCase();
    if (normalized.includes("failed to fetch") || normalized.includes("networkerror")) {
      return isEn
        ? "We could not connect to the API. Verify backend is running and try again."
        : "No pudimos conectar con la API. Verifica que backend este levantado e intenta nuevamente.";
    }
    return error.message;
  }
  return fallbackMessage;
}

export default function ShareClipPage() {
  const locale = useLocale();
  const isEn = locale === "en";
  const tr = useCallback((es: string, en: string) => (isEn ? en : es), [isEn]);
  const params = useParams<{ clipId: string }>();
  const clipId = params?.clipId ?? "";
  const draftKey = useMemo(() => getShareDraftKey(clipId, locale), [clipId, locale]);
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
  const [metadataTone, setMetadataTone] = useState<YoutubeMetadataSuggestionTone>("neutral");
  const [isSuggestingMetadata, setIsSuggestingMetadata] = useState(false);
  const [youtubeHashtags, setYoutubeHashtags] = useState<string[]>([]);
  const [youtubeTags, setYoutubeTags] = useState<string[]>([]);
  const [youtubeMetadataProvider, setYoutubeMetadataProvider] = useState<string | null>(null);
  const [youtubePublishStatus, setYoutubePublishStatus] = useState<"idle" | "success" | "error">("idle");
  const [youtubePublishMessage, setYoutubePublishMessage] = useState<string | null>(null);
  const [youtubePublishedUrl, setYoutubePublishedUrl] = useState<string | null>(null);
  const canPublishClip = clip ? ["done", "completed"].includes(clip.status.toLowerCase()) : false;
  const toneOptions = useMemo(
    () => [
      { value: "neutral" as const, label: tr("Neutral", "Neutral") },
      { value: "energetic" as const, label: tr("Energetico", "Energetic") },
      { value: "informative" as const, label: tr("Informativo", "Informative") }
    ],
    [tr]
  );

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      setError(tr("No encontramos una sesion activa para compartir este clip.", "No active session found to share this clip."));
      return;
    }

    let cancelled = false;

    const loadClip = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await videoApi.getMyClipById(clipId, token);
        const selectedClip = response.clip ?? null;

        if (!cancelled) {
          if (!selectedClip) {
            setError(tr("No encontramos el clip solicitado.", "Requested clip was not found."));
            setClip(null);
          } else {
            setClip(selectedClip);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(normalizeVideoError(loadError, tr("No pudimos cargar el clip para compartir.", "We could not load clip to share."), isEn));
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
  }, [clipId, token, tr, isEn]);

  useEffect(() => {
    if (!clip) {
      return;
    }

    let appliedDraft = false;

    try {
      const raw = window.localStorage.getItem(draftKey);
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<ShareYoutubeDraft>;
        if (typeof parsed.title === "string") {
          setYoutubeTitle(parsed.title);
          appliedDraft = true;
        }
        if (typeof parsed.description === "string") {
          setYoutubeDescription(parsed.description);
          appliedDraft = true;
        }
        if (parsed.privacy === "private" || parsed.privacy === "unlisted" || parsed.privacy === "public") {
          setYoutubePrivacy(parsed.privacy);
          appliedDraft = true;
        }
        if (parsed.tone === "neutral" || parsed.tone === "energetic" || parsed.tone === "informative") {
          setMetadataTone(parsed.tone);
          appliedDraft = true;
        }
        if (Array.isArray(parsed.hashtags)) {
          setYoutubeHashtags(parsed.hashtags.filter((item): item is string => typeof item === "string"));
          appliedDraft = true;
        }
        if (Array.isArray(parsed.tags)) {
          setYoutubeTags(parsed.tags.filter((item): item is string => typeof item === "string"));
          appliedDraft = true;
        }
        if (typeof parsed.provider === "string" || parsed.provider === null) {
          setYoutubeMetadataProvider(parsed.provider);
          appliedDraft = true;
        }
      }
    } catch {
      window.localStorage.removeItem(draftKey);
    }

    if (!appliedDraft) {
      setYoutubeTitle(`Clip ${clip.job_id.slice(0, 8)} - Hacelo Corto`);
      setYoutubeDescription(isEn ? `Clip generated from ${clip.source_filename}` : `Clip generado desde ${clip.source_filename}`);
      setYoutubeHashtags([]);
      setYoutubeTags([]);
      setYoutubeMetadataProvider(null);
      setMetadataTone("neutral");
      setYoutubePrivacy("private");
    }

    setYoutubePublishStatus("idle");
    setYoutubePublishMessage(null);
    setYoutubePublishedUrl(null);
  }, [clip, isEn, draftKey]);

  useEffect(() => {
    if (!clip) {
      return;
    }

    const payload: ShareYoutubeDraft = {
      title: youtubeTitle,
      description: youtubeDescription,
      privacy: youtubePrivacy,
      tone: metadataTone,
      hashtags: youtubeHashtags,
      tags: youtubeTags,
      provider: youtubeMetadataProvider
    };

    window.localStorage.setItem(draftKey, JSON.stringify(payload));
  }, [
    clip,
    draftKey,
    metadataTone,
    youtubeDescription,
    youtubeHashtags,
    youtubeMetadataProvider,
    youtubePrivacy,
    youtubeTags,
    youtubeTitle
  ]);

  const handleConnectYoutube = async () => {
    setInfo(null);
    try {
      const oauth = await authApi.getGoogleAuthUrl();
      window.sessionStorage.setItem("google_oauth_state", oauth.state);
      window.location.href = oauth.authorization_url;
    } catch {
      setError(tr("No pudimos iniciar la conexion con YouTube via Google OAuth.", "We could not start YouTube connection via Google OAuth."));
    }
  };

  const handlePublishYoutube = async () => {
    if (!token || !clip) {
      setError(tr("No hay sesion activa o clip seleccionado para publicar.", "No active session or selected clip to publish."));
      return;
    }

    setIsPublishingYoutube(true);
    setError(null);
    setInfo(null);
    setYoutubePublishStatus("idle");
    setYoutubePublishMessage(null);
    setYoutubePublishedUrl(null);

    try {
      const response = await videoApi.publishToYoutube(clip.job_id, token, {
        title: youtubeTitle.trim() || undefined,
        description: youtubeDescription.trim() || undefined,
        privacy: youtubePrivacy
      });

      setInfo(isEn ? `Published on YouTube: ${response.youtube_url}` : `Publicado en YouTube: ${response.youtube_url}`);
      setYoutubePublishStatus("success");
      setYoutubePublishedUrl(response.youtube_url);
      setYoutubePublishMessage(tr("Publicacion completada correctamente.", "Publishing completed successfully."));
    } catch (publishError) {
      setYoutubePublishStatus("error");
      setYoutubePublishMessage(
        normalizeVideoError(publishError, tr("No pudimos publicar el clip en YouTube.", "We could not publish clip on YouTube."), isEn)
      );
    } finally {
      setIsPublishingYoutube(false);
    }
  };

  const handleSuggestYoutubeMetadata = async () => {
    if (!token || !clip) {
      setError(tr("No hay sesion activa o clip seleccionado para generar metadata.", "No active session or selected clip to generate metadata."));
      return;
    }

    setIsSuggestingMetadata(true);
    setError(null);
    setInfo(null);

    try {
      const suggestion = await videoApi.suggestYoutubeMetadata(clip.job_id, token, metadataTone, locale);
      setYoutubeTitle(suggestion.title);
      setYoutubeDescription(suggestion.description);
      setYoutubeHashtags(suggestion.hashtags);
      setYoutubeTags(suggestion.tags);
      setYoutubeMetadataProvider(suggestion.provider);
      setInfo(
        isEn
          ? `Suggested metadata applied (${suggestion.generated_with_ai ? "AI" : "template"}).`
          : `Metadata sugerida aplicada (${suggestion.generated_with_ai ? "IA" : "template"}).`
      );
    } catch (suggestError) {
      setError(
        normalizeVideoError(
          suggestError,
          tr("No pudimos generar metadata sugerida para YouTube.", "We could not generate suggested metadata for YouTube."),
          isEn
        )
      );
    } finally {
      setIsSuggestingMetadata(false);
    }
  };

  return (
    <section className="w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      <Panel className="relative overflow-hidden border-neon-mint/25 bg-gradient-to-r from-night-900 via-night-800/80 to-night-900 p-5 sm:p-6">
        <div className="pointer-events-none absolute -right-14 -top-20 h-52 w-52 animate-drift rounded-full bg-neon-cyan/12 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 -left-10 h-52 w-52 animate-drift rounded-full bg-neon-violet/12 blur-3xl [animation-delay:400ms]" />

        <div className="relative animate-fade-up">
          <p className="text-xs uppercase tracking-[0.25em] text-neon-mint/75">{tr("compartir clip", "share clip")}</p>
          <h1 className="mt-2 font-display text-2xl text-white sm:text-3xl">{tr("Publicacion por red social", "Social publishing")}</h1>
          <p className="mt-2 text-sm text-white/70">
            {tr(
              "Desde esta pantalla podras conectar la subida individual de un clip para cada red. Por ahora dejamos el flujo preparado.",
              "From this screen you can connect individual clip publishing for each network. The base flow is ready."
            )}
          </p>
        </div>

        {isLoading ? <p className="mt-4 text-sm text-white/70">{tr("Cargando clip...", "Loading clip...")}</p> : null}

      {error ? (
          <div className="mt-4 rounded-xl border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-sm text-rose-200">
            <p>{error}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-2 rounded-lg border border-rose-300/35 bg-rose-300/10 px-2.5 py-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-rose-100 transition hover:bg-rose-300/20"
            >
               {tr("Reintentar", "Retry")}
             </button>
          </div>
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
                  {tr("El clip todavia no tiene preview disponible.", "Clip preview is not available yet.")}
                </div>
              )}

              <div className="mt-3 space-y-1 text-xs text-white/75">
                 <p>{tr("Clip", "Clip")}: {clip.job_id}</p>
                 <p>{tr("Video", "Video")}: {clip.video_id}</p>
                 <p>{tr("Estado", "Status")}: {clip.status}</p>
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
                              ? tr("Validando conexion con YouTube...", "Checking YouTube connection...")
                              : isYoutubeConnected
                                ? tr("Cuenta vinculada", "Connected account") + `${youtubeStatus?.provider_username ? ` (${youtubeStatus.provider_username})` : ""}`
                                : tr("Cuenta pendiente de vincular", "Account pending connection")
                            : tr("Integracion en roadmap. Disponible proximamente.", "Integration on roadmap. Coming soon.")}
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-2 sm:min-w-[260px]">
                        <Button
                          className="h-9 px-3 py-2 text-xs"
                          variant={isYoutubeConnected ? "neutral" : "violet"}
                          disabled={!isYoutube || isLoadingYoutubeStatus}
                          onClick={isYoutube ? () => void handleConnectYoutube() : undefined}
                        >
                          {isYoutubeConnected ? tr("Reconectar", "Reconnect") : tr("Conectar", "Connect")}
                        </Button>
                        <Button
                          className="h-9 px-3 py-2 text-xs"
                          disabled={!isYoutube || !isYoutubeConnected || isPublishingYoutube || !canPublishClip}
                          onClick={isYoutube ? () => void handlePublishYoutube() : undefined}
                        >
                          {isPublishingYoutube ? tr("Publicando...", "Publishing...") : tr("Publicar clip", "Publish clip")}
                        </Button>
                      </div>
                    </div>

                    {isYoutube && youtubePublishStatus !== "idle" ? (
                      <div
                        className={[
                          "mt-3 rounded-lg border px-3 py-2 text-xs",
                          youtubePublishStatus === "success"
                            ? "border-emerald-300/45 bg-emerald-300/10 text-emerald-100"
                            : "border-rose-300/45 bg-rose-300/10 text-rose-100"
                        ].join(" ")}
                      >
                        <p className="inline-flex items-center gap-1.5 font-semibold uppercase tracking-[0.12em]">
                          {youtubePublishStatus === "success" ? <CheckCircle2 size={14} /> : <AlertTriangle size={14} />}
                          {youtubePublishStatus === "success" ? tr("Publicado", "Published") : tr("Fallo la publicacion", "Publishing failed")}
                        </p>
                        {youtubePublishMessage ? <p className="mt-1">{youtubePublishMessage}</p> : null}
                        {youtubePublishStatus === "success" && youtubePublishedUrl ? (
                          <a
                            href={youtubePublishedUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-2 inline-flex items-center gap-1 rounded-md border border-emerald-200/35 bg-emerald-200/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-emerald-100 transition hover:bg-emerald-200/20"
                          >
                            {tr("Ver en YouTube", "View on YouTube")}
                          </a>
                        ) : null}
                      </div>
                    ) : null}

                    {isYoutube && !canPublishClip ? (
                      <p className="mt-2 text-xs text-amber-200">{tr("Este clip debe estar en estado DONE para poder publicarse en YouTube.", "Clip must be DONE to publish on YouTube.")}</p>
                    ) : null}

                    {isYoutube ? (
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        <div className="sm:col-span-2 rounded-lg border border-neon-cyan/25 bg-gradient-to-r from-neon-cyan/8 to-neon-violet/8 p-3">
                           <p className="text-[11px] uppercase tracking-[0.16em] text-neon-cyan/85">{tr("Asistente IA", "AI assistant")}</p>
                          <div className="mt-2 grid gap-2 sm:grid-cols-2">
                            <label className="text-xs text-white/75">
                               {tr("Tono IA", "AI tone")}
                              <select
                                value={metadataTone}
                                onChange={(event) => setMetadataTone(event.target.value as YoutubeMetadataSuggestionTone)}
                                className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50"
                              >
                                {toneOptions.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            </label>
                            <div className="flex items-end">
                              <Button
                                className="h-9 w-full px-3 py-2 text-xs"
                                variant="cyan"
                                disabled={!isYoutubeConnected || isSuggestingMetadata || !canPublishClip}
                                onClick={() => void handleSuggestYoutubeMetadata()}
                              >
                                <Sparkles size={14} />
                                {isSuggestingMetadata ? tr("Generando...", "Generating...") : tr("Generar datos con IA", "Generate with AI")}
                              </Button>
                            </div>
                          </div>
                           <p className="mt-2 text-[11px] text-white/60">{tr("Completa titulo y descripcion sugeridos para acelerar la publicacion.", "Use suggested title and description to speed up publishing.")}</p>
                        </div>

                        <label className="text-xs text-white/75 sm:col-span-2">
                           {tr("Titulo", "Title")}
                          <input
                            value={youtubeTitle}
                            onChange={(event) => setYoutubeTitle(event.target.value.slice(0, 100))}
                            maxLength={100}
                            className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50"
                          />
                        </label>
                        <label className="text-xs text-white/75 sm:col-span-2">
                           {tr("Descripcion", "Description")}
                          <textarea
                            value={youtubeDescription}
                            onChange={(event) => setYoutubeDescription(event.target.value.slice(0, 5000))}
                            maxLength={5000}
                            rows={3}
                            className="mt-1 w-full resize-y rounded-lg border border-white/20 bg-night-900/80 px-3 py-2 text-xs text-white outline-none focus:border-neon-cyan/50"
                          />
                        </label>
                        <label className="text-xs text-white/75 sm:col-span-2">
                           {tr("Privacidad", "Privacy")}
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

                        {(youtubeHashtags.length > 0 || youtubeTags.length > 0) ? (
                          <div className="sm:col-span-2 rounded-lg border border-white/12 bg-night-900/60 p-3 text-xs text-white/75">
                            {youtubeMetadataProvider ? (
                              <p className="text-[11px] uppercase tracking-[0.15em] text-neon-cyan/80">Provider: {youtubeMetadataProvider}</p>
                            ) : null}
                            {youtubeHashtags.length > 0 ? (
                              <div className="mt-2">
                                <p className="text-[11px] uppercase tracking-[0.12em] text-white/60">{tr("Hashtags sugeridos", "Suggested hashtags")}</p>
                                <div className="mt-1 flex flex-wrap gap-1.5">
                                  {youtubeHashtags.map((hashtag) => (
                                    <span
                                      key={hashtag}
                                      className="rounded-full border border-neon-cyan/35 bg-neon-cyan/10 px-2 py-0.5 text-[11px] text-neon-cyan"
                                    >
                                      {hashtag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                            {youtubeTags.length > 0 ? (
                              <div className="mt-2">
                                <p className="text-[11px] uppercase tracking-[0.12em] text-white/60">{tr("Tags sugeridos", "Suggested tags")}</p>
                                <div className="mt-1 flex flex-wrap gap-1.5">
                                  {youtubeTags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="rounded-full border border-neon-violet/35 bg-neon-violet/10 px-2 py-0.5 text-[11px] text-neon-violet"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                          </div>
                        ) : null}
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
                 {tr("Volver a biblioteca", "Back to library")}
               </Link>
            </div>
          </div>
        ) : null}
      </Panel>
    </section>
  );
}
