import { Settings, X } from "lucide-react";
import  {  useState } from "react";

export default function ModalSetings() {
    const [open, setOpen] = useState(false)
    const bool = (event: FormDataEntryValue | null) => event === "on";
    
    const handleSubmit =(event:FormData) =>{
        const data = {
            recorteVertical: bool(event.get("recorte9-16")),
            subtitulos: bool(event.get("subtitulo")),
            seguimientoFacil: bool(event.get("seguimientoFacial")),
            filtroColor: bool(event.get("filtroColor")),
            videoInicio: Number(event.get("videoInicio")),
            videoFin: Number(event.get("videoFin"))
        }
        console.log(data)
        setOpen(false)
    }

    return (<>
        <button onClick={() => setOpen(true)} className="flex gap-2 justify-center items-center rounded-lg border py-2 px-3 border-white/10 bg-white/5">
            <Settings size={16} />
            Configuración
        </button>
        {open && (

            <div className="fixed inset-0 z-50 flex items-center justify-center">
                <div onClick={() => setOpen(false)} className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
                <div className="relative p-6  border border-white/10 bg-[#22325A] rounded-2xl">
                    {/* header */}
                    <div className="flex items-center justify-between">
                        <h2>Configruaciones del video</h2>
                        <button onClick={() => setOpen(false)}><X size={18} /></button>

                    </div>
                    <form action={handleSubmit} className="w-full max-w-5xl mx-auto p-4 space-y-4">

                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" name="recorte9-16" className="peer hidden" />

                            <div className="w-5 h-5 rounded-md border border-white/30 
                                        peer-checked:bg-cyan-600 
                                        peer-checked:border-cyan-600 
                                        flex items-center justify-center">

                                <svg
                                    className="w-3 h-3 text-white opacity-0 peer-checked:opacity-100"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="3"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M5 13l4 4L19 7" />
                                </svg>

                            </div>

                            <span>Recorte 9:16</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" name="subtitulo" className="peer hidden" />

                            <div className="w-5 h-5 rounded-md border border-white/30 
                                        peer-checked:bg-cyan-600 
                                        peer-checked:border-cyan-600 
                                        flex items-center justify-center">

                                <svg
                                    className="w-3 h-3 text-white opacity-0 peer-checked:opacity-100"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="3"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M5 13l4 4L19 7" />
                                </svg>

                            </div>

                            <span>Subtitulo</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" name="seguimientoFacial" className="peer hidden" />

                            <div className="w-5 h-5 rounded-md border border-white/30 
                                        peer-checked:bg-cyan-600 
                                        peer-checked:border-cyan-600 
                                        flex items-center justify-center">

                                <svg
                                    className="w-3 h-3 text-white opacity-0 peer-checked:opacity-100"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="3"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M5 13l4 4L19 7" />
                                </svg>

                            </div>

                            <span>Seguimiento facial</span>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input type="checkbox" name="filtroColor" className="peer hidden" />

                            <div className="w-5 h-5 rounded-md border border-white/30 
                                        peer-checked:bg-cyan-600 
                                        peer-checked:border-cyan-600 
                                        flex items-center justify-center">

                                <svg
                                    className="w-3 h-3 text-white opacity-0 peer-checked:opacity-100"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="3"
                                    viewBox="0 0 24 24"
                                >
                                    <path d="M5 13l4 4L19 7" />
                                </svg>

                            </div>

                            <span>Filtros de color</span>
                        </label>

                        {/* Controles */}
                        <div className="flex  mt-5 flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">

                            <div className="flex gap-3">
                                <div className="flex items-center gap-2">
                                    <label className="text-xs text-white/60">Inicio</label>
                                    <input
                                        type="number"
                                        name="videoInicio"
                                        className="w-24 rounded-lg bg-white/5 border border-white/10 px-2 py-1"
                                    />
                                </div>

                                <div className="flex items-center gap-2">
                                    <label className="text-xs text-white/60">Fin</label>
                                    <input
                                        type="number"
                                        name="videoFin"
                                        className="w-24 rounded-lg bg-white/5 border border-white/10 px-2 py-1"
                                    />
                                </div>
                            </div>

                            <button className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500">
                                Recortar video
                            </button>
                        </div>
                    </form>

                </div>

            </div>

        )}
    </>)

}