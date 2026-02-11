import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Space Grotesk"', '"Segoe UI"', "sans-serif"],
        display: ['"Sora"', '"Segoe UI"', "sans-serif"],
      },
      colors: {
        night: {
          950: "#060b16",
          900: "#0a1020",
          800: "#121a2e",
          700: "#1b2740",
        },
        neon: {
          cyan: "#35d0ff",
          magenta: "#ff4fd8",
          violet: "#6f7cff",
          mint: "#4bffd2",
        },
      },
      boxShadow: {
        glow: "0 10px 35px rgba(53, 208, 255, 0.24)",
        panel: "0 20px 60px rgba(5, 8, 20, 0.55)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        drift: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.55s ease-out both",
        drift: "drift 5s ease-in-out infinite",
      },
    }
  },
  plugins: []
};

export default config;
