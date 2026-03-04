import type { Metadata } from "next";
import type { ReactNode } from "react";
import Script from "next/script";
import { getLocale, getMessages } from "next-intl/server";
import { NextIntlClientProvider } from "next-intl";
import { ThemeProvider } from "@/src/components/theme/ThemeProvider";
import { ThemeToggle } from "@/src/components/theme/ThemeToggle";
import { LanguageSwitcher } from "@/src/components/i18n/LanguageSwitcher";
import "./globals.css";

function resolveMetadataBase() {
  const fallbackUrl = "http://localhost:3000";
  const configuredUrl = process.env.NEXT_PUBLIC_SITE_URL?.trim();

  if (!configuredUrl) {
    return new URL(fallbackUrl);
  }

  try {
    return new URL(configuredUrl);
  } catch {
    return new URL(fallbackUrl);
  }
}

export async function generateMetadata(): Promise<Metadata> {
  const locale = await getLocale();
  const isEn = locale === "en";

  return {
    metadataBase: resolveMetadataBase(),
    title: {
      default: isEn ? "Hacelo Corto | Turn long videos into shorts" : "Hacelo Corto | Convierte videos largos en shorts",
      template: "%s | Hacelo Corto"
    },
    description: isEn
      ? "Turn long videos into publish-ready shorts: upload, timeline trim, audio edit, library and export in one app."
      : "Convierte videos largos en shorts listos para publicar: upload, recorte en timeline, edicion de audio, biblioteca y exportacion desde una sola app.",
    alternates: {
      canonical: "/"
    },
    robots: {
      index: true,
      follow: true
    },
    openGraph: {
      type: "website",
      locale: isEn ? "en_US" : "es_AR",
      url: "/",
      siteName: "Hacelo Corto",
      title: isEn ? "Hacelo Corto | Turn long videos into shorts" : "Hacelo Corto | Convierte videos largos en shorts",
      description: isEn
        ? "Web platform to create shorts from long videos with smart trim, manual timeline, audio editor and export."
        : "Plataforma web para crear shorts desde videos largos con recorte inteligente, timeline manual, audio editor y exportacion.",
      images: [
        {
          url: "/opengraph-image",
          width: 1200,
          height: 630,
          alt: isEn ? "Hacelo Corto - Turn long videos into shorts" : "Hacelo Corto - Convierte videos largos en shorts"
        }
      ]
    },
    twitter: {
      card: "summary_large_image",
      title: isEn ? "Hacelo Corto | Turn long videos into shorts" : "Hacelo Corto | Convierte videos largos en shorts",
      description: isEn
        ? "Upload, trim, audio and export in one app for creators publishing shorts."
        : "Upload, recorte, audio y exportacion en una sola app para creadores que publican shorts.",
      images: ["/twitter-image"]
    },
    icons: {
      icon: "/icon.svg"
    }
  };
}

type RootLayoutProps = {
  children: ReactNode;
};

export default async function RootLayout({ children }: RootLayoutProps) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <Script id="theme-init" strategy="beforeInteractive">
          {`(() => {
            const key = "hc-theme";
            const saved = localStorage.getItem(key);
            const isLight = saved ? saved === "light" : window.matchMedia("(prefers-color-scheme: light)").matches;
            const theme = isLight ? "light" : "dark";
            document.documentElement.classList.remove("light", "dark");
            document.documentElement.classList.add(theme);
            document.documentElement.setAttribute("data-theme", theme);
          })();`}
        </Script>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <ThemeProvider>
            {children}
            <div className="fixed bottom-4 right-4 z-50 flex items-center gap-2">
              <LanguageSwitcher />
              <ThemeToggle compact />
            </div>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
