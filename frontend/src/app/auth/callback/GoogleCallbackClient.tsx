"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertCircle, LoaderCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/src/store/useAuthStore";

const processedOAuthCodes = new Set<string>();

export function GoogleCallbackClient() {
  const t = useTranslations("auth");
  const router = useRouter();
  const searchParams = useSearchParams();
  const completeGoogleAuth = useAuthStore((state) => state.completeGoogleAuth);
  const clearError = useAuthStore((state) => state.clearError);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const [callbackMessage, setCallbackMessage] = useState<string | null>(null);
  const [isWaiting, setIsWaiting] = useState(true);

  useEffect(() => {
    const runCallback = async () => {
      clearError();
      setCallbackMessage(null);
      setIsWaiting(true);

      const callbackError = searchParams.get("error");
      const callbackCode = searchParams.get("code");
      const callbackState = searchParams.get("state");

      if (callbackError) {
        setCallbackMessage(t("oauthCanceled"));
        setIsWaiting(false);
        return;
      }

      if (!callbackCode || !callbackState) {
        setCallbackMessage(t("oauthMissingData"));
        setIsWaiting(false);
        return;
      }

      const storedState = window.sessionStorage.getItem("google_oauth_state");

      if (!storedState || storedState !== callbackState) {
        setCallbackMessage(t("oauthInvalidState"));
        setIsWaiting(false);
        return;
      }

      if (processedOAuthCodes.has(callbackCode)) {
        return;
      }

      processedOAuthCodes.add(callbackCode);

      const didAuthenticate = await completeGoogleAuth(callbackCode, callbackState);
      if (didAuthenticate) {
        window.sessionStorage.removeItem("google_oauth_state");
        router.replace("/app");
        return;
      }

      setCallbackMessage(t("oauthCompleteError"));
      setIsWaiting(false);
    };

    void runCallback();
  }, [clearError, completeGoogleAuth, router, searchParams, t]);

  const message = isLoading ? t("oauthLoading") : error ?? callbackMessage ?? t("oauthValidating");
  const shouldShowActions = !isWaiting && !isLoading;

  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-10 sm:px-8">
      <section className="relative mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-2xl items-center">
        <article className="w-full rounded-3xl border border-white/10 bg-night-900/60 p-6 text-white shadow-panel backdrop-blur-xl sm:p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-neon-cyan/80">{t("oauthLabel")}</p>
          <h1 className="mt-4 font-display text-3xl">{t("oauthTitle")}</h1>

          <div className="mt-6 flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-4 text-sm text-white/85">
            {isWaiting || isLoading ? <LoaderCircle className="mt-0.5 h-5 w-5 animate-spin text-neon-cyan" /> : <AlertCircle className="mt-0.5 h-5 w-5 text-rose-300" />}
            <p>{message}</p>
          </div>

          {shouldShowActions ? (
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/auth/login" className="rounded-xl border border-neon-cyan/40 bg-neon-cyan/10 px-4 py-2 text-sm font-semibold text-neon-cyan transition hover:bg-neon-cyan/20">
                {t("backToLogin")}
              </Link>
              <Link href="/auth/register" className="rounded-xl border border-white/20 bg-white/5 px-4 py-2 text-sm font-semibold text-white/80 transition hover:bg-white/10">
                {t("goRegister")}
              </Link>
            </div>
          ) : null}
        </article>
      </section>
    </main>
  );
}
