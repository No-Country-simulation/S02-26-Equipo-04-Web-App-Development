  import { useVideoSettingsStore, type VideoSettings } from "@/src/store/useVideoSettingsStore";
import { Button } from "../ui/Button";
import { FormEvent, useState } from "react";
const settingItems: Array<{ key: keyof VideoSettings; label: string }> = [
  { key: "cropToVertical", label: "Recorte 9:16" },
  { key: "subtitles", label: "Subtitulos" },
  { key: "faceTracking", label: "Seguimiento facial" },
  { key: "colorFilter", label: "Filtro de color" }
];
type GeneratedClipsSectionProps = {

  onProcessVideo: () => Promise<void>;
};
export function VideoSettings({onProcessVideo}:GeneratedClipsSectionProps){
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
                    <Button onClick={onProcessVideo} type="submit" className="h-10 w-auto px-4">
                      Generar video
                    </Button>
                  </div>
                </form>
    </>)
}