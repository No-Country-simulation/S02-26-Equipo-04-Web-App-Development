import { Link } from "react-router";
import { useAuthStore } from "../store/useAuthStore";

export function AppHomePage() {
  const logout = useAuthStore((state) => state.logout);

  return (
    <section className="mx-auto flex min-h-screen w-full max-w-4xl flex-col justify-center gap-5 px-6 py-10">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-700">Zona protegida</p>
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">Home privada temporal</h1>
      <p className="max-w-2xl text-slate-600">
        Ruta segura habilitada para pruebas de navegacion. Aqui se montara el dashboard en proximos sprints.
      </p>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
          onClick={logout}
        >
          Cerrar sesion mock
        </button>
        <Link
          to="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          Ir a landing
        </Link>
      </div>
    </section>
  );
}
