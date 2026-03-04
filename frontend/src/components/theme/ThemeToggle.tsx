"use client";

import { SunMoon } from "lucide-react";
import { useTheme } from "@/src/components/theme/ThemeProvider";

type ThemeToggleProps = {
  compact?: boolean;
};

export function ThemeToggle({ compact = false }: ThemeToggleProps) {
  const { toggleTheme } = useTheme();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex items-center gap-2 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-sm font-semibold text-white/85 transition hover:bg-white/10 ${
        compact ? "h-10" : ""
      }`}
      aria-label="Cambiar tema"
      title="Cambiar tema"
    >
      <SunMoon size={16} />
      {!compact ? <span>Tema</span> : null}
    </button>
  );
}
