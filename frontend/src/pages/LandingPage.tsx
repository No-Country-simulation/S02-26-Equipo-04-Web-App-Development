import { Link } from "react-router";

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden px-4 pb-20 pt-8 sm:px-8">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-16 top-8 h-72 w-72 rounded-full bg-neon-cyan/15 blur-3xl" />
        <div className="absolute right-0 top-24 h-72 w-72 rounded-full bg-neon-violet/18 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-neon-magenta/12 blur-3xl" />
      </div>

      <div className="relative mx-auto w-full max-w-[1220px] space-y-10">
        <header className="animate-fade-up flex items-center justify-between rounded-2xl border border-white/10 bg-night-900/60 px-4 py-3 backdrop-blur-xl">
          <div>
            <p className="font-display text-xl text-white">Hacelo Corto</p>
            <p className="text-xs uppercase tracking-[0.24em] text-neon-cyan/70">video automation studio</p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/auth/login"
              className="rounded-lg border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-white/90 transition hover:bg-white/10"
            >
              Ingresar
            </Link>
            <Link
              to="/auth/register"
              className="inline-flex items-center gap-2 rounded-lg border border-neon-cyan/45 bg-neon-cyan/15 px-4 py-2 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/25"
            >
              Crear cuenta
              <span aria-hidden="true">{">"}</span>
            </Link>
          </div>
        </header>

        <section className="grid items-center gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <article className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-8 [animation-delay:80ms]">
            <div className="mb-5 flex flex-wrap gap-2">
              <Tag label="Registro rapido" color="cyan" />
              <Tag label="Upload horizontal" color="mint" />
              <Tag label="Jobs en progreso" color="violet" />
            </div>

            <h1 className="font-display text-[clamp(2.05rem,3.8vw,3.7rem)] leading-[1.05] tracking-tight text-white">
              Convierte videos largos en shorts verticales listos para publicar.
            </h1>
            <p className="mt-4 max-w-2xl text-[clamp(1rem,1.35vw,1.18rem)] leading-relaxed text-white/78">
              Sube un video, deja que la IA detecte momentos clave, sigue el progreso de tus jobs y descarga resultados en
              formato social.
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <Link
              to="/auth/register"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-xl border border-neon-cyan/45 bg-neon-cyan/15 px-6 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/25"
            >
              Empezar gratis
              <span aria-hidden="true">*</span>
            </Link>
            <Link
              to="/app"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-xl border border-neon-violet/45 bg-neon-violet/15 px-6 text-sm font-semibold text-white transition hover:bg-neon-violet/25"
            >
              Probar rutas seguras
              <span aria-hidden="true">[]</span>
            </Link>
            </div>

            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              <Metric title="+40%" subtitle="retencion" />
              <Metric title="4x" subtitle="clips por video" />
              <Metric title="1 panel" subtitle="todo el flujo" />
            </div>
          </article>

          <article className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-5 shadow-panel sm:p-6 [animation-delay:140ms]">
            <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/70">Sprint 1</p>
            <h2 className="mt-2 font-display text-[clamp(1.4rem,1.9vw,2rem)] text-white">Historias priorizadas</h2>

            <div className="mt-4 space-y-3">
              {[
                "HU registro de usuario y login",
                "Subida de video horizontal",
                "Lista de jobs y estado en progreso",
                "Descarga de resultado final",
                "Mensajes claros en caso de error",
              ].map((item) => (
                <article key={item} className="rounded-xl border border-white/15 bg-white/5 px-4 py-3 text-sm text-white/85">
                  <div className="inline-flex items-center gap-2">
                    <span aria-hidden="true" className="text-neon-mint">
                      +
                    </span>
                    {item}
                  </div>
                </article>
              ))}
            </div>
          </article>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-7 [animation-delay:260ms]">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/55">Workflow</p>
              <h3 className="font-display text-[clamp(1.7rem,2.8vw,2.35rem)] text-white">De upload a descarga en 4 pasos</h3>
            </div>
            <span className="inline-flex items-center gap-2 rounded-lg border border-neon-cyan/45 bg-neon-cyan/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-neon-cyan">
              <span aria-hidden="true">*</span>
              MVP ready
            </span>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <StepBox
              step="01"
              title="Sube tu video"
              detail="Carga horizontal en pocos segundos con validacion inicial."
            />
            <StepBox
              step="02"
              title="Procesa con IA"
              detail="Recorte vertical, deteccion de foco y subtitulos automaticos."
            />
            <StepBox
              step="03"
              title="Monitorea jobs"
              detail="Consulta estado queued, processing, done o error."
            />
            <StepBox
              step="04"
              title="Descarga y publica"
              detail="Obtiene clips finales listos para TikTok, Reels y Shorts."
            />
          </div>
        </section>
      </div>
    </div>
  );
}

function Tag({ label, color }: { label: string; color: "cyan" | "mint" | "violet" }) {
  const tones = {
    cyan: "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan",
    mint: "border-neon-mint/45 bg-neon-mint/15 text-neon-mint",
    violet: "border-neon-violet/45 bg-neon-violet/15 text-neon-violet",
  };

  return <span className={`rounded-lg border px-2.5 py-1 text-xs font-semibold ${tones[color]}`}>{label}</span>;
}

function Metric({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="rounded-xl border border-white/15 bg-white/5 px-3 py-3">
      <p className="font-display text-[clamp(1.2rem,1.4vw,1.55rem)] text-white">{title}</p>
      <p className="text-xs uppercase tracking-[0.16em] text-white/55">{subtitle}</p>
    </div>
  );
}

function StepBox({ step, title, detail }: { step: string; title: string; detail: string }) {
  return (
    <article className="rounded-xl border border-white/12 bg-white/5 p-4">
      <p className="text-sm font-semibold text-neon-mint">{step}</p>
      <h4 className="mt-2 text-lg font-semibold text-white">{title}</h4>
      <p className="mt-2 text-sm text-white/75">{detail}</p>
    </article>
  );
}
