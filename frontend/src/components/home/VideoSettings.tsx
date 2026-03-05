import { useVideoSettingsStore, type VideoSettings as TimelineVideoSettings } from "@/src/store/useVideoSettingsStore";
import { useLocale } from "next-intl";
import { FormEvent, useState } from "react";
import { Button } from "../ui/Button";

type VideoSettingsProps = {
  trimStart: number;
  selectedVideoId: string | null;
  trimEnd: number;
  minClipDurationSec: number;
  isSubmitting: boolean;
  submitInfo: string | null;
  submitError: string | null;
  submitErrorSettings: string | null;
  submitInfoSettings: string | null;
  handleCreateJob: () => void;
  saveRaname: () => void;
  videoEditarBool: boolean;
  draftFilename: string;
  setDraftFilename: (event: string) => void;
};

type ClipOption = {
  value: TimelineVideoSettings["outputStyle"];
  label: string;
  description: string;
};

type ProfileOption = {
  value: TimelineVideoSettings["contentProfile"];
  label: string;
};

const clipOptions: ClipOption[] = [
  {
    value: "vertical",
    label: "Vertical 9:16",
    description: "Formato clasico para Shorts, Reels y TikTok"
  },
  {
    value: "speaker_split",
    label: "Speaker split",
    description: "Enfoque en hablante + plano general"
  }
];

const profileOptions: ProfileOption[] = [
  { value: "auto", label: "Auto" },
  { value: "interview", label: "Entrevista" },
  { value: "sports", label: "Deporte" },
  { value: "music", label: "Musica" }
];

export function VideoSettings({
  submitInfoSettings,
  submitErrorSettings,
  trimStart,
  videoEditarBool,
  draftFilename,
  setDraftFilename,
  saveRaname,
  trimEnd,
  minClipDurationSec,
  isSubmitting,
  submitInfo,
  submitError,
  selectedVideoId,
  handleCreateJob
}: VideoSettingsProps) {
  const isEn = useLocale() === "en";
  const tr = (es: string, en: string) => (isEn ? en : es);
  const settings = useVideoSettingsStore((state) => state.settings);
  const saveSettings = useVideoSettingsStore((state) => state.saveSettings);
  const [draft, setDraft] = useState<TimelineVideoSettings>(settings);
  const selectedDuration = Math.max(0, Math.ceil(trimEnd) - Math.floor(trimStart));
  const canCreateClip = Boolean(selectedVideoId) && selectedDuration >= minClipDurationSec;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    saveSettings(draft);
    saveRaname();
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="mt-5 space-y-4 min-w-70">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase tracking-[0.16em] text-white/60">{tr("Formato de salida", "Output format")}</p>
          <div className="mt-2 grid gap-2">
            {clipOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setDraft((prev) => ({ ...prev, outputStyle: option.value }))}
                className={[
                  "rounded-lg border px-3 py-2 text-left transition",
                  draft.outputStyle === option.value
                    ? "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
                    : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                ].join(" ")}
              >
                <p className="text-sm font-semibold">
                  {option.value === "vertical" ? tr("Vertical 9:16", "Vertical 9:16") : tr("Speaker split", "Speaker split")}
                </p>
                 <p className="mt-0.5 text-xs text-white/65">
                   {option.value === "vertical"
                     ? tr("Formato clasico para Shorts, Reels y TikTok", "Classic format for Shorts, Reels and TikTok")
                     : tr("Enfoque en hablante + plano general", "Focus speaker + wide shot")}
                 </p>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase tracking-[0.16em] text-white/60">{tr("Perfil de contenido", "Content profile")}</p>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {profileOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setDraft((prev) => ({ ...prev, contentProfile: option.value }))}
                className={[
                  "rounded-lg border px-3 py-2 text-sm font-semibold transition",
                  draft.contentProfile === option.value
                    ? "border-neon-mint/45 bg-neon-mint/15 text-neon-mint"
                    : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                ].join(" ")}
              >
                {option.value === "auto"
                  ? tr("Auto", "Auto")
                  : option.value === "interview"
                    ? tr("Entrevista", "Interview")
                    : option.value === "sports"
                      ? tr("Deporte", "Sports")
                      : tr("Musica", "Music")}
              </button>
            ))}
          </div>
        </div>

        <label className="block rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/90">
          <span className="text-xs uppercase tracking-[0.12em] text-white/65">{tr("Watermark", "Watermark")}</span>
          <input
            type="text"
            value={draft.watermark}
            onChange={(event) => {
              const value = event.target.value.slice(0, 12);
              setDraft((prev) => ({ ...prev, watermark: value }));
            }}
            maxLength={12}
            className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/70 px-3 py-2 text-xs text-white outline-none transition focus:border-neon-cyan/50"
          />
        </label>

        <label className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/90">
          <span>{tr("Subtitulos", "Subtitles")}</span>
          <input
            type="checkbox"
            checked={draft.subtitles}
            onChange={(event) => {
              const checked = event.target.checked;
              setDraft((prev) => ({ ...prev, subtitles: checked }));
            }}
            className="h-4 w-4 rounded border-white/20 bg-night-900 text-neon-cyan focus:ring-neon-cyan"
          />
        </label>

        {!videoEditarBool ? (
          <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
            <label>{tr("Nombre", "Name")}</label>
            <input
              value={draftFilename}
              onChange={(event) => setDraftFilename(event.target.value)}
              className="mt-1 w-full rounded-lg border border-white/20 bg-night-900/70 px-3 py-2 text-xs text-white outline-none transition focus:border-neon-cyan/50"
              maxLength={255}
              autoFocus
            />
            {submitInfoSettings ? <p className="mt-2 text-xs text-neon-mint">{submitInfoSettings}</p> : null}
            {submitErrorSettings ? <p className="mt-2 text-xs text-rose-200">{submitErrorSettings}</p> : null}
          </div>
        ) : null}

        <div className="flex items-center justify-end gap-2 pt-2">
          <Button type="submit" className="h-10 w-auto px-4">
            {tr("Guardar ajustes", "Save settings")}
          </Button>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
          <p>{tr("Recorte seleccionado", "Selected trim")}: {Math.floor(trimStart)}s - {Math.ceil(trimEnd)}s</p>
          <p className="mt-1 text-xs text-white/60">{tr("Duracion estimada", "Estimated duration")}: {selectedDuration}s ({tr("minimo", "minimum")} {minClipDurationSec}s)</p>
          <Button className="mt-3 w-auto px-4" onClick={handleCreateJob} disabled={isSubmitting || !canCreateClip}>
            {isSubmitting ? tr("Creando clip...", "Creating clip...") : tr("Generar clip con timeline", "Generate clip from timeline")}
          </Button>
          {!canCreateClip ? (
            <p className="mt-2 text-xs text-amber-200">{tr(`Ajusta el recorte para que tenga al menos ${minClipDurationSec}s.`, `Adjust trim so it is at least ${minClipDurationSec}s.`)}</p>
          ) : null}
          {submitInfo ? <p className="mt-2 text-xs text-neon-mint">{submitInfo}</p> : null}
          {submitError ? <p className="mt-2 text-xs text-rose-200">{submitError}</p> : null}
        </div>
      </form>
    </>
  );
}
