import Link from "next/link";
import { HaceloCortoLogo } from "@/src/components/branding/HaceloCortoLogo";

export default function HomePage() {
  const snapshot = [
    { label: "Estado", value: "Web app operativa" },
    { label: "Flujo", value: "Upload -> Edit -> Export" },
    { label: "Salida", value: "Clips listos para compartir" }
  ];

  const perfiles = [
    {
      titulo: "Auto detectar",
      descripcion: "Perfil por defecto en Home. Crea clips automaticos sin configurar reglas manuales.",
      tono: "cyan" as const
    },
    {
      titulo: "Entrevista",
      descripcion: "Prioriza tomas estables para dialogo y contenido tipo talking head.",
      tono: "mint" as const
    },
    {
      titulo: "Deportes",
      descripcion: "Usa framing mas abierto para no perder accion en escenas rapidas.",
      tono: "violet" as const
    },
    {
      titulo: "Musica",
      descripcion: "Ajuste para clips ritmicos y momentos destacados de performance.",
      tono: "magenta" as const
    }
  ];

  const demos: Array<{
    titulo: string;
    detalle: string;
    filename: string;
    path: string;
  }> = [
    {
      titulo: "Demo 01 - Upload 9:16 modo Musica",
      detalle: "Flujo Home: upload + perfil Musica.",
      filename: "video1_musica.mp4",
      path: "/landing-demos/video1_musica.mp4"
    },
    {
      titulo: "Demo 02 - Upload 9:16 modo Entrevista",
      detalle: "Framing estable para talking head y dialogo con perfil Entrevista.",
      filename: "video2_entrevista.mp4",
      path: "/landing-demos/video2_entrevista.mp4"
    },
    {
      titulo: "Demo 04 - Metadata IA para YouTube",
      detalle: "Sugerencias automaticas de titulo, descripcion, hashtags y tags.",
      filename: "video4_generando_texto_hastag_IA.mp4",
      path: "/landing-demos/video4_generando_texto_hastag_IA.mp4"
    },
    {
      titulo: "Demo 05 - Biblioteca de audios",
      detalle: "Subida y gestion de pistas para reutilizar en el editor de audio.",
      filename: "video5_subida_audio.mp4",
      path: "/landing-demos/video5_subida_audio.mp4"
    }
  ];

  const studioDemos = [
    {
      titulo: "Timeline Editor",
      detalle: "Ajuste manual de rango temporal, control de parametros y envio directo del job de recorte.",
      filename: "video3_timeline.mp4",
      path: "/landing-demos/video3_timeline.mp4"
    },
    {
      titulo: "Audio Editor",
      detalle: "Mezcla de audio sobre video con control de offset, rango, volumen y preview del render final.",
      filename: "video6_añade_audio_a_video.mp4",
      path: "/landing-demos/video6_añade_audio_a_video.mp4"
    }
  ];

  const faq = [
    {
      q: "Que esta funcionando hoy en la app?",
      a: "Login/registro, upload de video, jobs automaticos por perfiles, edicion manual en timeline, biblioteca de clips/videos/audios, audio editor y centro de exportacion."
    },
    {
      q: "La app ya se integra con YouTube?",
      a: "Si. Incluye conexion OAuth con Google, sugerencias de metadata con IA y flujo de publicacion desde la vista de compartir."
    },
    {
      q: "Puedo usar perfiles de contenido?",
      a: "Si. En Home hay perfiles Auto, Entrevista, Deportes y Musica, junto con estilo Vertical o Speaker Split."
    },
    {
      q: "Donde veo los resultados de cada job?",
      a: "En Panel y Biblioteca, con estados de cola/proceso/listo/error y acceso a vista de compartir/exportar."
    }
  ];

  return (
    <div className="relative min-h-screen overflow-hidden px-4 pb-24 pt-8 sm:px-8">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-20 top-4 h-80 w-80 rounded-full bg-neon-cyan/16 blur-3xl" />
        <div className="absolute right-[-4rem] top-16 h-96 w-96 rounded-full bg-neon-violet/16 blur-3xl" />
        <div className="absolute bottom-[-4rem] left-1/3 h-80 w-80 rounded-full bg-neon-magenta/12 blur-3xl" />
      </div>

      <div className="relative mx-auto w-full max-w-[1220px] space-y-12">
        <header className="animate-fade-up flex items-center justify-between rounded-2xl border border-white/10 bg-night-900/60 px-4 py-3 backdrop-blur-xl">
          <Link href="/" className="inline-flex items-center" aria-label="Ir al home">
            <HaceloCortoLogo variant="wordmark" className="h-8 w-auto text-white sm:h-9" title="Hacelo Corto" />
          </Link>
          <div className="flex items-center gap-2">
            <Link
              href="/auth/login"
              className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-white/90 transition hover:bg-white/10"
            >
              Ingresar
            </Link>
            <Link
              href="/auth/register"
              className="inline-flex items-center gap-2 rounded-xl border border-neon-cyan/45 bg-neon-cyan/15 px-4 py-2 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/25"
            >
              Crear cuenta
              <span aria-hidden="true">*</span>
            </Link>
          </div>
        </header>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-7 shadow-panel sm:p-10 [animation-delay:80ms]">
          <div className="mx-auto max-w-5xl text-center">
            <div className="mb-5 flex flex-wrap gap-2">
              <Tag label="App web operativa" color="cyan" />
              <Tag label="Flujo end-to-end" color="mint" />
              <Tag label="Catppuccin UI" color="violet" />
            </div>

            <h1 className="font-display text-[clamp(2.4rem,7.5vw,6.6rem)] leading-[0.96] tracking-tight text-white">
              Convierte videos largos en
              <span className="bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-violet bg-clip-text text-transparent">
                {" "}shorts listos para publicar
              </span>
            </h1>
            <p className="mx-auto mt-5 max-w-3xl text-[clamp(1rem,1.35vw,1.24rem)] leading-relaxed text-white/78">
              Hacelo Corto concentra en una sola app web el flujo completo: subir video, generar clips con perfiles de
              contenido, editar en timeline, mezclar audio, gestionar biblioteca y exportar resultados.
            </p>

            <article className="mx-auto mt-8 max-w-3xl rounded-2xl border border-white/15 bg-night-800/65 p-3">
              <div className="flex flex-col gap-3 md:flex-row">
                <div className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-white/70">
                  Home: upload, estilo de clip, perfil de contenido, estado de jobs y acceso directo a biblioteca, timeline y export.
                </div>
                <Link
                  href="/auth/register"
                  className="inline-flex h-12 items-center justify-center rounded-xl border border-neon-cyan/45 bg-neon-cyan/15 px-6 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/25"
                >
                  Crear cuenta y probar
                </Link>
              </div>
              <div className="mt-3 flex flex-wrap justify-center gap-2 text-xs text-white/60">
                <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1">/app panel</span>
                <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1">/app/timeline</span>
                <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1">/app/library</span>
                <span className="rounded-lg border border-white/15 bg-white/5 px-2 py-1">/app/export</span>
              </div>
            </article>

            <div className="mt-7 grid gap-3 sm:grid-cols-3">
              {snapshot.map((item) => (
                <Metric key={item.label} title={item.value} subtitle={item.label} />
              ))}
            </div>
          </div>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-7 [animation-delay:130ms]">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/55">Flujo MVP</p>
              <h2 className="font-display text-[clamp(1.7rem,2.6vw,2.6rem)] text-white">Como se usa hoy en el producto</h2>
            </div>
            <span className="inline-flex items-center gap-2 rounded-lg border border-neon-cyan/45 bg-neon-cyan/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-neon-cyan">
              <span aria-hidden="true">*</span>
              basado en flujo real
            </span>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <StepBox
              step="01"
              title="Sube video"
              detail="Desde Panel, cargas un archivo y el backend registra el video para procesamiento."
            />
            <StepBox
              step="02"
              title="Genera jobs"
              detail="Seleccionas estilo (vertical o speaker split) y perfil (auto, entrevista, deportes, musica)."
            />
            <StepBox
              step="03"
              title="Sigue estado"
              detail="Ves cola/proceso/listo/error en panel y biblioteca con polling y refresco de resultados."
            />
              <StepBox
                step="04"
                title="Edita, mezcla y exporta"
                detail="Puedes ajustar timeline, usar audio editor y cerrar flujo desde biblioteca o centro de exportacion."
              />
          </div>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-7 [animation-delay:260ms]">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-white/55">Perfiles y estilos</p>
              <h3 className="font-display text-[clamp(1.7rem,2.8vw,2.35rem)] text-white">Configuraciones activas en Home</h3>
            </div>
            <span className="inline-flex items-center gap-2 rounded-lg border border-neon-cyan/45 bg-neon-cyan/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-neon-cyan">
              <span aria-hidden="true">#</span>
              sincronizado con app
            </span>
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {perfiles.map((perfil) => (
              <UseCaseCard key={perfil.titulo} titulo={perfil.titulo} descripcion={perfil.descripcion} tono={perfil.tono} />
            ))}
          </div>

          <div className="mt-4 rounded-2xl border border-white/12 bg-night-800/70 p-4 text-sm text-white/75">
            El panel prioriza `Auto detectar`; en timeline puedes ajustar rango temporal y opciones avanzadas para recorte
            manual cuando el caso necesita mas control.
          </div>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-7 [animation-delay:320ms]">
          <h3 className="text-center font-display text-[clamp(1.9rem,3.1vw,3rem)] text-white">Edicion avanzada en accion</h3>
          <p className="mx-auto mt-2 max-w-3xl text-center text-sm text-white/72">
            Dos espacios clave para cerrar el workflow: timeline para recorte fino y audio editor para mezcla final del clip.
          </p>

          <div className="mt-7 grid gap-5 lg:grid-cols-2">
            {studioDemos.map((demo) => (
              <article key={demo.titulo} className="rounded-2xl border border-white/12 bg-night-800/70 p-4">
                <div className="overflow-hidden rounded-xl border border-neon-violet/25 bg-black/45">
                  <video
                    autoPlay
                    muted
                    loop
                    playsInline
                    controls
                    preload="metadata"
                    src={demo.path}
                    className="aspect-video w-full object-cover"
                  />
                </div>
                <h4 className="mt-3 text-xl font-semibold text-white">{demo.titulo}</h4>
                <p className="mt-2 text-sm text-white/72">{demo.detalle}</p>
                <p className="mt-2 text-xs text-neon-violet/80">Archivo demo: {demo.filename}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-7 [animation-delay:340ms]">
          <h3 className="text-center font-display text-[clamp(1.7rem,2.7vw,2.7rem)] text-white">Demos reales del producto</h3>
          <p className="mx-auto mt-2 max-w-3xl text-center text-sm text-white/72">
            Flujos capturados sobre la app actual: perfiles por contenido, timeline, metadata con IA, audio editor y experiencia responsive.
          </p>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {demos.map((demo) => (
              <DemoSlot
                key={demo.titulo}
                titulo={demo.titulo}
                detalle={demo.detalle}
                filename={demo.filename}
                videoPath={demo.path}
              />
            ))}
          </div>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel sm:p-7 [animation-delay:360ms]">
          <div className="grid gap-5 lg:grid-cols-[0.52fr_1fr]">
            <h3 className="font-display text-[clamp(1.6rem,3vw,2.7rem)] text-white">Preguntas frecuentes</h3>
            <div className="space-y-3">
              {faq.map((item) => (
                <details key={item.q} className="rounded-xl border border-white/12 bg-night-800/70 px-4 py-3 text-white/85">
                  <summary className="cursor-pointer list-none text-base font-semibold text-white">{item.q}</summary>
                  <p className="mt-2 text-sm text-white/70">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/70 p-8 shadow-panel [animation-delay:420ms]">
          <div className="rounded-2xl border border-white/10 bg-gradient-to-r from-neon-violet/12 via-neon-cyan/10 to-neon-mint/12 p-8 text-center">
            <h3 className="font-display text-[clamp(2rem,4vw,3.2rem)] text-white">Crea clips profesionales hoy</h3>
            <p className="mx-auto mt-3 max-w-2xl text-white/75">
              Ya puedes usar el flujo end-to-end en produccion y validar resultados con demos reales del equipo.
            </p>
            <Link
              href="/auth/register"
              className="mx-auto mt-6 inline-flex h-12 items-center justify-center rounded-xl border border-neon-cyan/45 bg-neon-cyan/15 px-7 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/25"
            >
              Crear cuenta y empezar
            </Link>
          </div>
        </section>

        <footer className="grid gap-5 rounded-3xl border border-white/10 bg-night-900/55 p-6 md:grid-cols-3">
          <div>
            <p className="font-display text-xl text-white">Hacelo Corto</p>
            <p className="mt-2 text-sm text-white/65">Producto en evolucion continua con foco en recorte vertical, edicion y publicacion asistida.</p>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-white/70">Producto</p>
            <ul className="mt-2 space-y-1 text-sm text-white/70">
              <li>Panel de upload y jobs</li>
              <li>Timeline para recorte manual</li>
              <li>Biblioteca, audio editor y exportacion</li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-white/70">Acceso</p>
            <ul className="mt-2 space-y-1 text-sm text-white/70">
              <li>
                <Link href="/auth/login" className="hover:text-white">
                  Ingresar
                </Link>
              </li>
              <li>
                <Link href="/auth/register" className="hover:text-white">
                  Crear cuenta
                </Link>
              </li>
            </ul>
          </div>
        </footer>
      </div>
    </div>
  );
}

function Tag({ label, color }: { label: string; color: "cyan" | "mint" | "violet" }) {
  const tones = {
    cyan: "border-neon-cyan/45 bg-neon-cyan/15 text-neon-cyan",
    mint: "border-neon-mint/45 bg-neon-mint/15 text-neon-mint",
    violet: "border-neon-violet/45 bg-neon-violet/15 text-neon-violet"
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

function UseCaseCard({
  titulo,
  descripcion,
  tono
}: {
  titulo: string;
  descripcion: string;
  tono: "cyan" | "violet" | "mint" | "magenta";
}) {
  const tonos = {
    cyan: "border-neon-cyan/35 bg-neon-cyan/12",
    violet: "border-neon-violet/35 bg-neon-violet/12",
    mint: "border-neon-mint/35 bg-neon-mint/12",
    magenta: "border-neon-magenta/35 bg-neon-magenta/12"
  };

  return (
    <article className={`rounded-xl border p-4 ${tonos[tono]}`}>
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-lg font-semibold text-white">{titulo}</h4>
        <span aria-hidden="true" className="text-white/65">
          {"->"}
        </span>
      </div>
      <p className="mt-2 text-sm text-white/75">{descripcion}</p>
    </article>
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

function DemoSlot({
  titulo,
  detalle,
  filename,
  videoPath
}: {
  titulo: string;
  detalle: string;
  filename: string;
  videoPath: string;
}) {
  return (
    <article className="rounded-2xl border border-white/12 bg-night-800/70 p-4">
      <div className="overflow-hidden rounded-xl border border-neon-cyan/25 bg-black/45">
        <video controls preload="metadata" src={videoPath} className="aspect-video w-full object-cover" />
      </div>
      <div>
        <h4 className="mt-3 text-base font-semibold text-white">{titulo}</h4>
        <p className="mt-2 text-sm text-white/72">{detalle}</p>
        <p className="mt-2 text-xs text-neon-cyan/80">Archivo demo: {filename}</p>
      </div>
    </article>
  );
}
