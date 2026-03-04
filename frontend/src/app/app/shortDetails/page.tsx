"use client";

import { getProtectedRedirect } from '@/src/router/redirects'
import { useAuthStore } from '@/src/store/useAuthStore'
import { Clock3, Copy, Hash, Share2 } from 'lucide-react'
import { useTranslations } from 'next-intl'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

// const statusStyles = {
//   listo: 'border-neon-mint/40 bg-neon-mint/10 text-neon-mint',
//   revision: 'border-neon-magenta/40 bg-neon-magenta/10 text-neon-magenta',
//   render: 'border-neon-cyan/40 bg-neon-cyan/10 text-neon-cyan',
// }

export default function ShortDetailPage() {
    const t = useTranslations("app");
    const router = useRouter();
    
    const bootstrapSession = useAuthStore((state) => state.bootstrapSession);
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const isBootstrapped = useAuthStore((state) => state.isBootstrapped);
    useEffect(() => {
        void bootstrapSession();
    }, [bootstrapSession]);
     useEffect(() => {
            const redirectPath = isBootstrapped ? getProtectedRedirect(isAuthenticated) : null;
    
            if (redirectPath) {
                router.replace(redirectPath);
            }
        }, [isAuthenticated, isBootstrapped, router]);
    
        if (!isBootstrapped || !isAuthenticated) {
            return null;
        }
    

//   const { shortId = '' } = useParams()
//   const short = useShortById(shortId)
//   const pushToast = useToastStore((state) => state.pushToast)

//   if (!short) return <Navigate to="/app/panel" replace />

  return (
    <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
      <section className="rounded-2xl border border-white/10 bg-night-800/55 p-5 shadow-panel">
        <p className="text-xs uppercase tracking-[0.22em] text-neon-cyan/70">{t("shortDetailsTag")}</p>
        {/* <h2 className="mt-1 font-display text-xl text-white">{short.title}</h2> */}
        <div className="mt-4 grid place-items-center rounded-xl border border-white/15 bg-night-900/55 p-4">
          <div className="relative aspect-[9/16] w-full max-w-[18rem] rounded-xl border border-neon-cyan/35 bg-night-900/85">
            <div className="absolute inset-0 rounded-xl bg-[radial-gradient(circle_at_28%_22%,rgba(53,208,255,0.22),transparent_45%),radial-gradient(circle_at_72%_82%,rgba(255,79,216,0.2),transparent_45%)]" />
            <div className="absolute bottom-3 left-3 rounded-md border border-white/20 bg-night-950/85 px-2 py-1 text-[11px] text-white/75">
              {t("previewFormat")}
            </div>
          </div>
        </div>
        <div className="mt-4 flex items-center justify-between text-sm text-white/75">
          {/* <span>{short.duration} - {short.format}</span>
          <span className={`rounded-full border px-2 py-1 text-[11px] uppercase ${statusStyles[short.status]}`}>
            {short.status}
          </span> */}
        </div>
      </section>

      <section className="rounded-2xl border border-white/10 bg-night-800/55 p-5 shadow-panel">
        <p className="text-xs uppercase tracking-[0.22em] text-neon-magenta/70">{t("quickActions")}</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            // onClick={() => pushToast({ type: 'info', title: 'Hashtags generados', message: 'Sugerencias listas.' })}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-neon-magenta/45 bg-neon-magenta/10 px-3 py-2 text-sm font-semibold text-neon-magenta"
          >
            <Hash size={14} />
            {t("hashtags")}
          </button>
          <button
            type="button"
            // onClick={() => pushToast({ type: 'info', title: 'Texto copiado', message: 'Caption copiado al portapapeles.' })}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-neon-cyan/45 bg-neon-cyan/10 px-3 py-2 text-sm font-semibold text-neon-cyan"
          >
            <Copy size={14} />
            {t("copyCaption")}
          </button>
          <button
            type="button"
            // onClick={() => pushToast({ type: 'success', title: 'Programado', message: 'Se agenda para hoy 18:00.' })}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-neon-mint/45 bg-neon-mint/10 px-3 py-2 text-sm font-semibold text-neon-mint"
          >
            <Clock3 size={14} />
            {t("scheduleUpload")}
          </button>
          <button
            type="button"
            // onClick={() => pushToast({ type: 'success', title: 'Subida iniciada', message: 'Publicando en redes conectadas.' })}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-2 text-sm font-semibold text-neon-cyan"
          >
            <Share2 size={14} />
            {t("publishNow")}
          </button>
        </div>

        <div className="mt-5 rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-white/80">
          <p className="font-semibold text-white">{t("inspector")}</p>
          {/* <p className="mt-2">Preset: {short.preset}</p> */}
          {/* <p>Subtitulos: {short.subtitles}</p>
          <p>Plataformas: {short.platforms.join(', ')}</p>
          <p>Horario: {short.schedule ?? 'Sin programar'}</p> */}
        </div>
      </section>
    </div>
  )
}
