import Link from "next/link";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <section className="mx-auto flex min-h-screen w-full max-w-3xl flex-col items-center justify-center gap-4 px-6 text-center">
        <p className="rounded-full border border-red-500/30 bg-red-100 px-3 py-1 text-sm font-medium text-red-700">
          Error de ruta
        </p>
        <h1 className="text-3xl font-bold text-slate-900">404 / Ruta no encontrada</h1>
        <p className="max-w-xl text-slate-600">
          La pagina que buscas no existe o no esta disponible.
        </p>
        <Link
          href="/"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
        >
          Volver al inicio
        </Link>
      </section>
    </main>
  );
}
