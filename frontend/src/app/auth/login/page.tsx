"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Eye, EyeOff, KeyRound, Mail, ShieldCheck, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { getPublicOnlyRedirect } from "@/src/router/redirects";
import { useAuthStore } from "@/src/store/useAuthStore";
import Image from "next/image";
import { Button } from "@/src/components/ui/Button";
import { AuthApiError, authApi } from "@/src/services/authApi";

export default function LoginPage() {
  const t = useTranslations("auth");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const login = useAuthStore((state) => state.login);
  const bootstrapSession = useAuthStore((state) => state.bootstrapSession);
  const clearError = useAuthStore((state) => state.clearError);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
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
    setLocalError(null);

    const didLogin = await login(email, password);
    if (didLogin) {
      router.replace("/app");
    }
  };

  const handleGoogleLogin = async () => {
    setLocalError(null);
    clearError();
    setIsGoogleLoading(true);

    try {
      const { authorization_url, state } = await authApi.getGoogleAuthUrl();
      window.sessionStorage.setItem("google_oauth_state", state);
      window.location.href = authorization_url;
    } catch (requestError) {
      const message = requestError instanceof AuthApiError ? requestError.message : t("googleStartError");
      setLocalError(message);
      setIsGoogleLoading(false);
    }
  };

  const formError = localError ?? error;

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-10 sm:px-8">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-20 top-16 h-72 w-72 animate-drift rounded-full bg-neon-cyan/15 blur-3xl" />
        <div className="absolute right-0 top-1/4 h-72 w-72 rounded-full bg-neon-violet/20 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-neon-magenta/10 blur-3xl" />
      </div>

      <section className="relative mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-6xl items-center gap-8 lg:grid-cols-[1.05fr_0.95fr]">
        <article className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/60 p-6 shadow-panel backdrop-blur-xl sm:p-8">
          <p className="inline-flex items-center gap-2 rounded-full border border-neon-cyan/35 bg-neon-cyan/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-neon-cyan">
            <Sparkles className="h-3.5 w-3.5" />
            {t("secureAccess")}
          </p>

          <h1 className="mt-5 font-display text-[clamp(2rem,3.2vw,3rem)] leading-tight text-white">{t("loginTitle")}</h1>
          {/* <p className="mt-3 max-w-xl text-sm leading-relaxed text-white/75 sm:text-base">
            Entra a tu workspace para gestionar subidas, monitorear jobs y descargar tus clips procesados.
          </p> */}

          <div className="mt-4 grid grid-cols-2 gap-2 rounded-xl border border-white/10 bg-white/5 p-1">

            <Link
              href="/auth/login"
              className="rounded-lg bg-neon-cyan/15 px-3 py-2 text-center text-sm font-semibold text-neon-cyan transition"
            >
              {t("tabsLogin")}
            </Link>

            <Link
              href="/auth/register"
              className="rounded-lg px-3 py-2 text-center text-sm font-semibold text-white/70 transition hover:bg-white/5 hover:text-white"
            >
              {t("tabsRegister")}
            </Link>

          </div>
          <form className="mt-7 space-y-4" onSubmit={handleSubmit}>
            <label className="block space-y-2">
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">{t("email")}</span>
              <span className="flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3">
                <Mail className="h-4 w-4 text-neon-cyan" />
                <input
                  type="email"
                  placeholder={t("emailPlaceholder")}
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value);
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
              <span className="text-xs font-semibold uppercase tracking-[0.18em] text-white/55">{t("password")}</span>
              <span className="flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-3">
                <KeyRound className="h-4 w-4 text-neon-violet" />
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="********"
                  value={password}
                  autoComplete="current-password"
                  onChange={(event) => {
                    setPassword(event.target.value);
                    if (error) {
                      clearError();
                    }
                  }}
                  className="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/35"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((currentValue) => !currentValue)}
                  className="text-white/55 transition hover:text-neon-cyan"
                  aria-label={showPassword ? t("hidePassword") : t("showPassword")}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </span>
            </label>
             {formError ? <p className="text-sm font-medium text-rose-300">{formError}</p> : null}

            <Button type="submit" className="mt-6" disabled={isLoading}>
              <ShieldCheck className="h-4 w-4" />
              {isLoading ? t("loggingIn") : t("loginAction")}
            </Button>
          </form>
          <Button type="button" variant="neutral" className="mt-6" onClick={handleGoogleLogin} disabled={isLoading || isGoogleLoading}>
            {isGoogleLoading ? t("redirectingGoogle") : t("continueGoogle")}
            <Image loading="eager" width={20} height={20} src="https://img.icons8.com/fluency/48/google-logo.png" alt="google-logo" />

          </Button>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-sm text-white/65">
            <p>
              <Link href="" className="font-semibold text-neon-cyan underline decoration-neon-cyan/40 underline-offset-4">
                {t("forgotPassword")}
              </Link>
            </p>

            <Link href="/" className="inline-flex items-center gap-2 text-white/70 transition hover:text-neon-mint">
              <ArrowLeft className="h-4 w-4" />
              {t("backToLanding")}
            </Link>
          </div>
        </article>

        <aside className="animate-fade-up rounded-3xl border border-white/10 bg-night-900/50 p-6 shadow-panel [animation-delay:120ms] sm:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-neon-mint/80">{t("accessIncludes")}</p>
          <ul className="mt-5 space-y-3 text-sm text-white/80">
            {[
              t("accessItem1"),
              t("accessItem2"),
              t("accessItem3")
            ].map((item) => (
              <li key={item} className="rounded-xl border border-white/12 bg-white/5 px-4 py-3">
                {item}
              </li>
            ))}
          </ul>
        </aside>
      </section>
    </main>
  );
}
