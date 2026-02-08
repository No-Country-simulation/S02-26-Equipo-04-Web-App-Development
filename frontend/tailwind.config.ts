import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          100: "#d6f5f5",
          500: "#118a8a",
          700: "#0a5252"
        }
      }
    }
  },
  plugins: []
};

export default config;
