import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#0284C7",
          50: "#082F49",
          100: "#0C4A6E",
          400: "#38BDF8",
          500: "#0EA5E9",
          600: "#0284C7",
          700: "#0369A1",
        },
        cyber: {
          cyan: "#06B6D4",
          blue: "#3B82F6",
          purple: "#8B5CF6",
          emerald: "#10B981",
          rose: "#F43F5E",
          amber: "#F59E0B",
        },
        secondary: "#06B6D4",
        accent: "#F59E0B",
        ink: {
          DEFAULT: "var(--text-primary)",
          muted: "var(--text-muted)",
          dim: "#64748B",
        },
        surface: {
          DEFAULT: "var(--bg-page)",
          card: "var(--card-bg)",
          hover: "var(--card-hover)",
          subtle: "var(--card-subtle)",
        },
      },
      boxShadow: {
        card: "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
        pop: "0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6)",
        glow: "0 0 25px -5px rgba(6, 182, 212, 0.3)",
        "glow-rose": "0 0 25px -5px rgba(244, 63, 94, 0.3)",
        "glow-emerald": "0 0 25px -5px rgba(16, 185, 129, 0.3)",
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "var(--font-inter)", "Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-jakarta)", "Plus Jakarta Sans", "sans-serif"],
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
