import { useVideoSettingsStore, type VideoSettings } from "@/src/store/useVideoSettingsStore";
import { Button } from "../ui/Button";
import { FormEvent, useState } from "react";


type ButtonGeneraRecorte={
  trimStart :number,
  selectedVideoId: string | null,
  trimEnd:number,
  minClipDurationSec:number,
  isSubmitting:boolean,
  submitInfo:string  | null, 
  submitError:string| null,
  submitErrorSettings:string | null,
  submitInfoSettings:string | null,
  handleCreateJob:() => void,
  saveRaname:() => void,
  videoEditarBool:boolean,
  draftFilename:string,
  setDraftFilename:(event:string) => void
}

const settingItems: Array<{ key: keyof VideoSettings; label: string }> = [
  { key: "cropToVertical", label: "Recorte 9:16" },
  { key: "subtitles", label: "Subtitulos" },
  { key: "faceTracking", label: "Seguimiento facial" },
  { key: "colorFilter", label: "Filtro de color" }
];

export function VideoSettings( {submitInfoSettings,submitErrorSettings, trimStart,videoEditarBool,draftFilename,setDraftFilename, saveRaname,  trimEnd, minClipDurationSec, isSubmitting,  submitInfo, submitError,selectedVideoId,handleCreateJob}:ButtonGeneraRecorte){
      const settings = useVideoSettingsStore((state) => state.settings);
      const saveSettings = useVideoSettingsStore((state) => state.saveSettings);
      const [draft, setDraft] = useState<VideoSettings>(settings);
      const selectedDuration = Math.max(0, Math.ceil(trimEnd) - Math.floor(trimStart));
      const canCreateClip = Boolean(selectedVideoId) && selectedDuration >= minClipDurationSec;
      
     const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        saveSettings(draft);
        saveRaname()
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
    {
          !videoEditarBool&&(
            <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
              <label className="">
                Nombre
              </label>
              <input
                  value={draftFilename}
                  onChange={(event) => setDraftFilename(event.target.value)}
                  className="w-full rounded-lg border border-white/20 bg-night-900/70 px-3 mt-1 py-2 text-xs text-white outline-none transition focus:border-neon-cyan/50"
                  maxLength={255}
                  autoFocus
                  />
                                     {submitInfoSettings ? <p className="mt-2 text-xs text-neon-mint">{submitInfoSettings}</p> : null}
                    {submitErrorSettings ? <p className="mt-2 text-xs text-rose-200">{submitErrorSettings}</p> : null}
          </div>)}

                  <div className="flex flex-wrap items-center justify-end gap-2 pt-2">
                    {/* <Button
                      type="button"
                      variant="neutral"
                      className="h-10 w-auto px-4"
                      onClick={() => {
                        resetSettings();
                        setDraft(useVideoSettingsStore.getState().settings);
                      }}
                    >
                      Restaurar
                    </Button> */}
                    <Button type="submit"  className="h-10 w-auto px-4">
                      Guardar ajustes
                    </Button>

                  </div>


          <div className="mt-4 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-white/80">
            <p>Recorte seleccionado: {Math.floor(trimStart)}s - {Math.ceil(trimEnd)}s</p>
            <p className="mt-1 text-xs text-white/60">Duracion estimada: {selectedDuration}s (minimo {minClipDurationSec}s)</p>
            <Button className="mt-3 w-auto px-4" onClick={handleCreateJob} disabled={isSubmitting || !canCreateClip}>
              {isSubmitting ? "Creando clip..." : "Generar clip con timeline"}
            </Button>
            {!canCreateClip ? (
              <p className="mt-2 text-xs text-amber-200">Ajusta el recorte para que tenga al menos {minClipDurationSec}s.</p>
            ) : null}
            {submitInfo ? <p className="mt-2 text-xs text-neon-mint">{submitInfo}</p> : null}
            {submitError ? <p className="mt-2 text-xs text-rose-200">{submitError}</p> : null}
          </div> 
                </form>
    </>)
}
