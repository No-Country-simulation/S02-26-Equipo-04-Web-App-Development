"use client";

import { Button } from "@/src/components/ui/Button";
import { useVideoSettingsStore, type VideoSettings } from "@/src/store/useVideoSettingsStore";
import { Settings2, X } from "lucide-react";
import { FormEvent, useState } from "react";

const settingItems: Array<{ key: keyof VideoSettings; label: string }> = [
  { key: "cropToVertical", label: "Recorte 9:16" },
  { key: "subtitles", label: "Subtitulos" },
  { key: "faceTracking", label: "Seguimiento facial" },
  { key: "colorFilter", label: "Filtro de color" }
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
              <div className="space-y-2">
                {settingItems.map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white/90"
                  >
                    <span>{item.label}</span>
                    <input
                      type="checkbox"
                      checked={draft[item.key] as boolean}
                      onChange={(event) => {
                        const checked = event.target.checked;
                        setDraft((prev) => ({ ...prev, [item.key]: checked }));
                      }}
                      className="h-4 w-4 rounded border-white/20 bg-night-900 text-neon-cyan focus:ring-neon-cyan"
                    />
                  </label>
                ))}
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <label className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                  <span className="text-xs uppercase tracking-[0.18em] text-white/60">Inicio (seg)</span>
                  <input
                    type="number"
                    min={0}
                    value={draft.videoStart}
                    onChange={(event) => {
                      const value = Number(event.target.value);
                      setDraft((prev) => ({ ...prev, videoStart: Number.isFinite(value) ? value : 0 }));
                    }}
                    className="mt-2 w-full rounded-lg border border-white/15 bg-night-900/90 px-2 py-1.5 text-sm text-white outline-none transition focus:border-neon-cyan"
                  />
                </label>

                <label className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">
                  <span className="text-xs uppercase tracking-[0.18em] text-white/60">Fin (seg)</span>
                  <input
                    type="number"
                    min={0}
                    value={draft.videoEnd}
                    onChange={(event) => {
                      const value = Number(event.target.value);
                      setDraft((prev) => ({ ...prev, videoEnd: Number.isFinite(value) ? value : 0 }));
                    }}
                    className="mt-2 w-full rounded-lg border border-white/15 bg-night-900/90 px-2 py-1.5 text-sm text-white outline-none transition focus:border-neon-cyan"
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
