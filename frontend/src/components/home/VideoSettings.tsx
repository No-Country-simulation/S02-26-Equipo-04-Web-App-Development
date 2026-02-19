import { useVideoSettingsStore, type VideoSettings } from "@/src/store/useVideoSettingsStore";
import { Button } from "../ui/Button";
import { FormEvent, useState } from "react";
const settingItems: Array<{ key: keyof VideoSettings; label: string }> = [
  { key: "cropToVertical", label: "Recorte 9:16" },
  { key: "subtitles", label: "Subtitulos" },
  { key: "faceTracking", label: "Seguimiento facial" },
  { key: "colorFilter", label: "Filtro de color" }
];

export function VideoSettings(){
      const settings = useVideoSettingsStore((state) => state.settings);
      const saveSettings = useVideoSettingsStore((state) => state.saveSettings);
      const resetSettings = useVideoSettingsStore((state) => state.resetSettings);
        const [draft, setDraft] = useState<VideoSettings>(settings);
      
     const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        saveSettings(draft);
      };
    return (<>
    
                <form onSubmit={handleSubmit} className="mt-5 space-y-4 min-w-70">
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
    
                  {/* <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
     */}
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
    </>)
}