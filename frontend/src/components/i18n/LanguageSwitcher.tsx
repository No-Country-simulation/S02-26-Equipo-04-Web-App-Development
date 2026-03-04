"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { locales } from "@/src/i18n/locales";
import { setLocaleAction } from "@/src/app/actions/setLocale";

export function LanguageSwitcher() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations("common");
  const [isPending, startTransition] = useTransition();

  const handleLocaleChange = (nextLocale: string) => {
    if (nextLocale === locale) {
      return;
    }

    startTransition(async () => {
      await setLocaleAction(nextLocale);
      router.refresh();
    });
  };

  return (
    <div className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-night-900/70 px-2 py-1.5 text-xs text-white/85 backdrop-blur">
      <span className="px-1 text-white/60">{t("language")}</span>
      {locales.map((entry) => {
        const active = entry === locale;
        const label = entry === "es" ? t("spanish") : t("english");

        return (
          <button
            key={entry}
            type="button"
            onClick={() => handleLocaleChange(entry)}
            disabled={isPending}
            className={`rounded-lg px-2 py-1 transition ${
              active ? "bg-neon-cyan/20 text-neon-cyan" : "text-white/70 hover:bg-white/10 hover:text-white"
            }`}
            aria-pressed={active}
            aria-label={label}
          >
            {entry.toUpperCase()}
          </button>
        );
      })}
    </div>
  );
}
