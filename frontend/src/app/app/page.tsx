"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getProtectedRedirect } from "@/src/router/redirects";
import { useAuthStore } from "@/src/store/useAuthStore";

export default function AppHomePage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);
  const router = useRouter();

  useEffect(() => {
    const redirectPath = getProtectedRedirect(isAuthenticated);

    if (redirectPath) {
      router.replace(redirectPath);
    }
  }, [isAuthenticated, router]);

  const handleLogout = () => {
    logout();
    router.replace("/");
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <section className="mx-auto flex min-h-screen w-full max-w-4xl flex-col justify-center gap-5 px-6 py-10">
      {/* <p className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-700">Zona protegida</p>
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">Home privada temporal</h1>
      <p className="max-w-2xl text-slate-600">
        Ruta segura habilitada para pruebas de navegacion. Aqui se montara el dashboard en proximos sprints.
      </p>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
          onClick={handleLogout}
        >
          Cerrar sesion mock
        </button>
        <Link
          href="/"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          Ir a landing
        </Link>
      </div> */}
     </section>
  );
}
