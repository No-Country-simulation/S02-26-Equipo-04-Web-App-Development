import { Link, useNavigate } from "react-router";
import { useAuthStore } from "../store/useAuthStore";

export function LoginPage() {
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleDemoLogin = () => {
    login();
    navigate("/app", { replace: true });
  };

  return (
    <section className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center gap-5 px-6 py-10">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Acceso</p>
      <h1 className="text-3xl font-bold tracking-tight text-slate-900">Iniciar sesion</h1>
      <p className="text-sm text-slate-600">
        Vista temporal de login. El equipo de auth reemplazara este componente.
      </p>

      <button
        type="button"
        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
        onClick={handleDemoLogin}
      >
        Entrar en modo demo
      </button>

      <p className="text-sm text-slate-600">
        No tienes cuenta?{" "}
        <Link to="/auth/register" className="font-semibold text-slate-900 underline decoration-slate-400 underline-offset-4">
          Registrate
        </Link>
      </p>
      <Link to="/" className="text-sm font-medium text-slate-600 underline decoration-slate-300 underline-offset-4">
        Volver a la landing
      </Link>
    </section>
  );
}
