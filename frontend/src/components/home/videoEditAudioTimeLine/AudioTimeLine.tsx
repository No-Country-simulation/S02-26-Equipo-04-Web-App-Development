import { Pause, Play } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import WaveSurfer from "wavesurfer.js"
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js"

type PropTimeLine = {
  videoDurationSec: number,
  selectedAudioUrl: string | null,
regionChange?: (start: number, end: number) => void

}
export function AudioTimeLine({
  videoDurationSec,
  selectedAudioUrl,
  regionChange
}: PropTimeLine) {
  const wsRef = useRef<WaveSurfer | null>(null)
  const regionsRef = useRef<InstanceType<typeof RegionsPlugin> | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)
    const [isPlaying, setIsPlaying] = useState(false);
  
const regionRef = useRef<ReturnType<
  InstanceType<typeof RegionsPlugin>["addRegion"]
> | null>(null)
  // ✅ 1️⃣ Crear instancia SOLO una vez
  useEffect(() => {
    if (!containerRef.current) return

    // 🔥 limpiar contenedor SIEMPRE
    containerRef.current.innerHTML = ""

    const regions = RegionsPlugin.create()

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "rgb(200, 0, 200)",
      progressColor: "rgb(100, 0, 100)",
      plugins: [regions],
    })

    wsRef.current = ws
    regionsRef.current = regions

    return () => {
    //   ws.destroy()
      wsRef.current = null
      regionsRef.current = null
    }
  }, []) // 👈 solo una vez

  // ✅ 2️⃣ Cargar audio cuando cambia
  useEffect(() => {
    if (!wsRef.current) return
    if (!selectedAudioUrl) return

    const ws = wsRef.current

    ws.load(selectedAudioUrl)

    ws.once("ready", () => {
      regionsRef.current?.clearRegions()

      const region =regionsRef.current?.addRegion({
        start: 0,
        end: videoDurationSec,
        minLength: videoDurationSec - 0.1,
        maxLength: videoDurationSec,
        content: "Resize me",
        color: "rgba(180, 120, 255, 0.25)",
        drag: true,
        resize: false,
      })
      if(region){
        regionRef.current = region

      }
      // 🔥 Escuchar cuando el usuario termina de mover
      region?.on("update-end", () => {
        const { start, end } = region
        regionChange?.(Math.floor(start),Math.floor( end))
      })
    })
  }, [selectedAudioUrl,videoDurationSec,regionChange]) 
 const playRegion = () => {
    // const regions = regionsRef.current?.getRegions()
    // const firstRegion = regions ? Object.values(regions)[0] : null
  const ws = wsRef.current

    if (ws?.isPlaying()) {
        setIsPlaying(false)
    ws.pause()
  } else {
    setIsPlaying(true)
    ws?.play(
      regionRef.current?.start,
      regionRef.current?.end
    )
  }
  }

  return (
    <div>
        <div ref={containerRef} />
      
            {/* <button onClick={playRegion}>Play selección</button> */}
            
        <button
          type="button"
         onClick={playRegion}
          className="inline-flex h-10 w-10 items-center justify-center self-center rounded-full border border-neon-violet/45 bg-neon-violet/15 text-neon-violet transition hover:bg-neon-violet/25"
          aria-label={isPlaying ? "Pausar audio" : "Reproducir audio"}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
        </button>
        
    </div>
  )
}