import { Loader } from "@/src/components/ui/Loader";
import ModalSetings from "../layout/ModalSetings";

type ProjectStatusPanelProps = {
  hasVideo: boolean;
  isUploading: boolean;
};

export function ProjectStatusPanel({ hasVideo, isUploading }: ProjectStatusPanelProps) {
  const status = isUploading ? "Procesando" : hasVideo ? "Video cargado" : "Sin video";
  const progress = isUploading ? 45 : hasVideo ? 100 : 0;

  return (
    <section>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/80">estado del proyecto</p>
          <h3 className="mt-1 font-display text-2xl text-white">{status}</h3>
        </div>
        {/* <span className="rounded-lg border border-neon-violet/45 bg-neon-violet/15 px-3 py-1 text-xs font-semibold text-white">
          Mock
        </span> */}
      </div>

      <div className="mt-4 rounded-xl border border-white/15 bg-white/5 p-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-white/80">Progreso</span>
          <span className="text-white">{progress}%</span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-night-950/90">
          <div
            className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-violet transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <ul className="mt-4 space-y-2 text-sm text-white/80">
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Upload recibido</li>
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Analisis de escenas</li>
        <li className="rounded-xl border border-white/10 bg-white/5 px-3 py-2">Generacion de clips</li>
      </ul>
      <div className="mt-4 ">
        <ModalSetings/>
      </div>
          
      {isUploading ? <Loader className="mt-4" label="Analizando video en segundo plano..." /> : null}
    </section>
  );
}
