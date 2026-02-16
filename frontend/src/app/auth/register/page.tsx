"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, CircleCheckBig, Mail, Rocket, UserRound } from "lucide-react";
import { getPublicOnlyRedirect } from "@/src/router/redirects";
import { useAuthStore } from "@/src/store/useAuthStore";
import { Button } from "@/src/components/ui/Button";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [repeatPassword, setRepeatPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const register = useAuthStore((state) => state.register);
  const bootstrapSession = useAuthStore((state) => state.bootstrapSession);
  const clearError = useAuthStore((state) => state.clearError);
  const isBootstrapped = useAuthStore((state) => state.isBootstrapped);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const router = useRouter();

  useEffect(() => {
    if (!isBootstrapped) {
      void bootstrapSession();
    }
  }, [bootstrapSession, isBootstrapped]);

  useEffect(() => {
    const redirectPath = getPublicOnlyRedirect(isAuthenticated);

    if (redirectPath) {
      router.replace(redirectPath);
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (password !== repeatPassword) {
      setLocalError("Las contrasenas no coinciden.");
      return;
    }

    setLocalError(null);
    const didRegister = await register(email, password);
    if (didRegister) {
      router.replace("/app");
    }
  };

  const formError = localError ?? error;

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-10 sm:px-8">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -right-20 top-12 h-72 w-72 animate-drift rounded-full bg-neon-violet/20 blur-3xl" />
        <div className="absolute left-0 top-1/3 h-72 w-72 rounded-full bg-neon-cyan/15 blur-3xl" />
        <div className="absolute bottom-0 right-1/3 h-64 w-64 rounded-full bg-neon-magenta/10 blur-3xl" />
      </div>

      <section className="relative mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center gap-8 lg:grid-cols-[0.95fr_1.05fr]">


        <article className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel backdrop-blur-xl [animation-delay:120ms] sm:p-8">
          <p className="inline-flex items-center gap-2 rounded-full border border-neon-violet/35 bg-neon-violet/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-neon-violet">
            <Rocket className="h-3.5 w-3.5" />
            Registro inicial
          </p>

          <h1 className="mt-5 font-display text-[clamp(2rem,3.2vw,3rem)] leading-tight text-white">Crear cuenta</h1>
          {/* <p className="mt-3 max-w-xl text-sm leading-relaxed text-white/75 sm:text-base">
            Esta pantalla queda lista para integrar validaciones, API de registro y activacion por email.
          </p> */}
          <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-white/10 bg-white/5 p-1">

            <Link
              href="/auth/login"
              className="   rounded-lg px-3 py-2 text-center text-sm font-semibold text-white/70 transition hover:bg-white/5 hover:text-white"
            >
              Iniciar sesión
            </Link>

            <Link
              href="/auth/register"
              className="rounded-lg bg-neon-cyan/15 px-3 py-2 text-center text-sm font-semibold text-neon-cyan transition "
            >
              Registrate
            </Link>

          </div>

          <form className="mt-7 space-y-4" onSubmit={handleSubmit}>
            <label className="block space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">Correo</span>
              <span className="flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3">
                <UserRound className="h-4 w-4 text-neon-mint" />
                <input
                  type="email"
                  placeholder="usuario@hacelocorto.com"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
                    setLocalError(null);
                    if (error) {
                      clearError();
                    }
                  }}
                  className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/35"
                  required
                />
              </span>
            </label>

            <label className="block space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">Contraseña</span>
              <span className="flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3">
                <Mail className="h-4 w-4 text-neon-cyan" />
                <input
                  type="password"
                  placeholder="*****"
                  value={password}
                  autoComplete="username"
                  onChange={(event) => {
                    setPassword(event.target.value);
                    setLocalError(null);
                    if (error) {
                      clearError();
                    }
                  }}
                  className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/35"
                  required
                />
              </span>

            </label>
            <label className="block space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">Repetir contraseña</span>
              <span className="flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3">
                <Mail className="h-4 w-4 text-neon-cyan" />
                <input
                  type="password"
                  placeholder="*****"
                  value={repeatPassword}
                  autoComplete="username"
                  onChange={(event) => {
                    setRepeatPassword(event.target.value);
                    setLocalError(null);
                    if (error) {
                      clearError();
                    }
                  }}
                  className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/35"
                  required
                />
              </span>

            </label>
            {formError ? <p className="text-sm font-medium text-rose-300">{formError}</p> : null}

            <Button type="submit" variant="violet" className="mt-6" disabled={isLoading}>
              {isLoading ? "Creando cuenta..." : "Crear cuenta"}
            </Button>
          </form>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-sm text-white/65">
            {/* <p>
              Ya tienes cuenta?{" "}
              <Link href="/auth/login" className="font-semibold text-neon-cyan underline decoration-neon-cyan/40 underline-offset-4">
                Inicia sesion
              </Link>
            </p> */}

            <Link href="/" className="inline-flex items-center gap-2 text-white/70 transition hover:text-neon-mint">
              <ArrowLeft className="h-4 w-4" />
              Volver a la landing
            </Link>
          </div>
        </article>
        <aside className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/50 p-6 shadow-panel sm:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-neon-violet/80">Onboarding</p>
          <h2 className="mt-3 font-display text-[clamp(1.8rem,2.8vw,2.6rem)] text-white">Activa tu cuenta en minutos</h2>

          <ul className="mt-6 space-y-3 text-sm text-white/80">
            {[
              "Configura perfil y preferencias de salida por red social.",
              "Conecta tu flujo de upload y procesamiento automatizado.",
              "Escala de pruebas a produccion sin cambiar la UI base."
            ].map((item) => (
              <li key={item} className="flex items-start gap-3 rounded-xl border border-white/12 bg-white/5 px-4 py-3">
                <CircleCheckBig className="mt-0.5 h-4 w-4 shrink-0 text-neon-mint" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </aside>
      </section>
    </main>
  );
}
