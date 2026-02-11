import { Link } from "react-router";

export function RegisterPage() {
  return (
    <section className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center gap-5 px-6 py-10">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Onboarding</p>
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">Crear cuenta</h1>
      <p className="text-sm text-slate-600">
        Vista temporal de registro. El equipo de auth implementara el formulario definitivo.
      </p>

      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700">
        Estructura lista para conectar con API de registro y validaciones de formulario.
      </div>

      <p className="text-sm text-slate-600">
        Ya tienes cuenta?{" "}
        <Link to="/auth/login" className="font-semibold text-slate-900 underline decoration-slate-400 underline-offset-4">
          Inicia sesion
        </Link>
      </p>
      <Link to="/" className="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4">
        Volver a la landing
      </Link>
    </section>
  );
}
