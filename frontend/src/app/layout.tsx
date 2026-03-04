import type { Metadata } from "next";
import type { ReactNode } from "react";
import Script from "next/script";
import { ThemeProvider } from "@/src/components/theme/ThemeProvider";
import { ThemeToggle } from "@/src/components/theme/ThemeToggle";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hacelo Corto",
  description: "Landing publica del equipo frontend",
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
