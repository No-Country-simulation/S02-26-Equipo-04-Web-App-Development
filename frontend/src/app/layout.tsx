import type { Metadata } from "next";
import type { ReactNode } from "react";
import Script from "next/script";
import { ThemeProvider } from "@/src/components/theme/ThemeProvider";
import { ThemeToggle } from "@/src/components/theme/ThemeToggle";
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

const metadataBase = resolveMetadataBase();

export const metadata: Metadata = {
  metadataBase,
  title: {
    default: "Hacelo Corto | Convierte videos largos en shorts",
    template: "%s | Hacelo Corto"
  },
  description:
    "Convierte videos largos en shorts listos para publicar: upload, recorte en timeline, edicion de audio, biblioteca y exportacion desde una sola app.",
  alternates: {
    canonical: "/"
  },
  robots: {
    index: true,
    follow: true
  },
  openGraph: {
    type: "website",
    locale: "es_AR",
    url: "/",
    siteName: "Hacelo Corto",
    title: "Hacelo Corto | Convierte videos largos en shorts",
    description:
      "Plataforma web para crear shorts desde videos largos con recorte inteligente, timeline manual, audio editor y exportacion.",
    images: [
      {
        url: "/opengraph-image",
        width: 1200,
        height: 630,
        alt: "Hacelo Corto - Convierte videos largos en shorts"
      }
    ]
  },
  twitter: {
    card: "summary_large_image",
    title: "Hacelo Corto | Convierte videos largos en shorts",
    description:
      "Upload, recorte, audio y exportacion en una sola app para creadores que publican shorts.",
    images: ["/twitter-image"]
  },
  icons: {
    icon: "/icon.svg"
  }
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="es" suppressHydrationWarning>
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
        <ThemeProvider>
          {children}
          <div className="fixed bottom-4 right-4 z-50">
            <ThemeToggle compact />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
