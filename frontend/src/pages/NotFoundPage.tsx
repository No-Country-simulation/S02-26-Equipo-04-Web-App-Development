import { Link, useRouteError } from "react-router";

export function NotFoundPage() {
  const error = useRouteError();
  const message =
    error instanceof Error
      ? error.message
      : "La pagina que buscas no existe o no esta disponible.";

  return (
    <section className="mx-auto flex min-h-screen w-full max-w-3xl flex-col items-center justify-center gap-4 px-6 text-center text-slate-100">
      <p className="rounded-full border border-neon-magenta/30 bg-neon-magenta/10 px-3 py-1 text-sm font-medium text-neon-magenta">
        Error de ruta
      </p>
      <h1 className="font-display text-3xl font-bold text-white">404 / Ruta no encontrada</h1>
      <p className="max-w-xl text-slate-300">{message}</p>
      <Link
        to="/"
        className="rounded-lg border border-neon-cyan/45 bg-neon-cyan/15 px-4 py-2 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/25"
      >
        Volver al inicio
      </Link>
    </section>
  );
}
