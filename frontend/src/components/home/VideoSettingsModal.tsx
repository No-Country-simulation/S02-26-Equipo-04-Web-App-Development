"use client";

import { Button } from "@/src/components/ui/Button";
import { useVideoSettingsStore, type VideoSettings } from "@/src/store/useVideoSettingsStore";
import { Settings2, X } from "lucide-react";
import { FormEvent, useState } from "react";

const profileOptions: Array<{ value: VideoSettings["contentProfile"]; label: string }> = [
  { value: "auto", label: "Auto" },
  { value: "interview", label: "Entrevista" },
  { value: "sports", label: "Deporte" },
  { value: "music", label: "Musica" }
];

export function VideoSettingsModal() {
  const settings = useVideoSettingsStore((state) => state.settings);
  const saveSettings = useVideoSettingsStore((state) => state.saveSettings);
  const resetSettings = useVideoSettingsStore((state) => state.resetSettings);
  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState<VideoSettings>(settings);

  const closeModal = () => setIsOpen(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    saveSettings(draft);
    closeModal();
  };

  return (
    <>
      <Button
        variant="neutral"
        className="h-10 w-auto px-4"
        onClick={() => {
          setDraft(settings);
          setIsOpen(true);
        }}
      >
        <Settings2 size={14} />
        Configuracion
      </Button>

      {isOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button
            type="button"
            className="absolute inset-0 bg-[#01030d]/70 backdrop-blur-sm"
            onClick={closeModal}
            aria-label="Cerrar modal de configuracion"
          />

          <div className="relative z-10 w-full max-w-lg rounded-2xl border border-white/15 bg-night-900/95 p-5 shadow-panel">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/80">ajustes de video</p>
                <h2 className="mt-1 font-display text-2xl text-white">Configuracion de procesamiento</h2>
              </div>

              <button
                type="button"
                onClick={closeModal}
                className="rounded-lg border border-white/15 p-2 text-white/70 transition hover:bg-white/10 hover:text-white"
                aria-label="Cerrar"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              <div className="space-y-3">
                <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/60">Formato</p>
                  <div className="mt-2 grid gap-2">
                    <button
                      type="button"
                      onClick={() => setDraft((prev) => ({ ...prev, outputStyle: "vertical" }))}
                      className={[
                        "rounded-lg border px-3 py-2 text-left text-sm font-semibold transition",
                        draft.outputStyle === "vertical"
                          ? "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
                          : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                      ].join(" ")}
                    >
                      Vertical 9:16
                    </button>
                    <button
                      type="button"
                      onClick={() => setDraft((prev) => ({ ...prev, outputStyle: "speaker_split" }))}
                      className={[
                        "rounded-lg border px-3 py-2 text-left text-sm font-semibold transition",
                        draft.outputStyle === "speaker_split"
                          ? "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan"
                          : "border-white/15 bg-night-900/70 text-white/80 hover:bg-white/10"
                      ].join(" ")}
                    >
                      Speaker split
                    </button>
                  </div>
                </div>

                <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-white/60">Perfil de contenido</p>
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
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                <label className="block rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/90">
                  <span className="text-xs uppercase tracking-[0.12em] text-white/65">Watermark</span>
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
                  <span>Subtitulos</span>
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
              </div>

              <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="neutral"
                  className="h-10 w-auto px-4"
                  onClick={() => {
                    resetSettings();
                    setDraft(useVideoSettingsStore.getState().settings);
                  }}
                >
                  Restaurar
                </Button>
                <Button type="submit" className="h-10 w-auto px-4">
                  Guardar ajustes
                </Button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
