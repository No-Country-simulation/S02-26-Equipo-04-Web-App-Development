"use client";

import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

type Theme = "dark" | "light";

type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: Theme;
  setTheme: (value: Theme) => void;
  toggleTheme: () => void;
};

const STORAGE_KEY = "hc-theme";

const ThemeContext = createContext<ThemeContextValue | null>(null);

function readSystemTheme(): Theme {
  if (typeof window === "undefined") {
    return "dark";
  }

  return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function applyThemeToDom(theme: Theme) {
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(theme);
  root.setAttribute("data-theme", theme);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") {
      return "dark";
    }

    const saved = window.localStorage.getItem(STORAGE_KEY);
    return saved === "light" || saved === "dark" ? saved : readSystemTheme();
  });
  useEffect(() => {
    applyThemeToDom(theme);
  }, [theme]);

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: light)");
    const onChange = () => {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === "light" || saved === "dark") {
        return;
      }
      const next = media.matches ? "light" : "dark";
      setThemeState(next);
    };

    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const setTheme = (value: Theme) => {
    window.localStorage.setItem(STORAGE_KEY, value);
    setThemeState(value);
  };

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme: theme,
      setTheme,
      toggleTheme: () => setTheme(theme === "dark" ? "light" : "dark")
    }),
    [theme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
