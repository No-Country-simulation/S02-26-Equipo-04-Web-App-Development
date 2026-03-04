"use server";

import { cookies } from "next/headers";
import { hasLocale } from "next-intl";
import { defaultLocale, locales } from "@/src/i18n/locales";

export async function setLocaleAction(nextLocale: string) {
  const locale = hasLocale(locales, nextLocale) ? nextLocale : defaultLocale;
  const cookieStore = await cookies();

  cookieStore.set("NEXT_LOCALE", locale, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax"
  });
}
