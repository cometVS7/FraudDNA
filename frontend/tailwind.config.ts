import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-display)", "Playfair Display", "DM Serif Display", "Georgia", "serif"],
        display: ["var(--font-display)", "Playfair Display", "DM Serif Display", "Georgia", "serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        // Midnight core palette
        obsidian: "#08080A",
        onyx: "#040406",
        carbon: "#121317",
        graphite: "#1C1D22",
        slate: "#2E3038",
        smoke: "#464853",
        ash: "#5E616E",
        steel: "#777A88",
        fog: "#9194A1",
        mist: "#ACAEB9",
        silver: "#C7C9D1",
        bone: "#E2E3E9",
        "paper-white": "#FFFFFF",
        copper: {
          DEFAULT: "#CC9166",
          hover: "#DE9F74",
          dim: "#A36F49",
        },
        gilded: {
          DEFAULT: "#AE9357",
          light: "#FFF0CC",
          glow: "rgba(174,147,87,0.2)",
        },

        // Semantic risk palette
        risk: {
          low: "#8FAF9B",
          review: "#C7A66B",
          high: "#C47A63",
          critical: "#D05B5B",
          info: "#A6A9B3",
        },

        // Compatibility system tokens mapped to midnight theme
        background: "#08080A",
        foreground: "#E2E3E9",
        card: {
          DEFAULT: "#040406",
          foreground: "#E2E3E9",
        },
        primary: {
          DEFAULT: "#FFFFFF",
          foreground: "#08080A",
        },
        secondary: {
          DEFAULT: "#121317",
          foreground: "#E2E3E9",
        },
        muted: {
          DEFAULT: "#121317",
          foreground: "#9194A1",
        },
        accent: {
          DEFAULT: "#1C1D22",
          foreground: "#CC9166",
        },
        destructive: {
          DEFAULT: "#D05B5B",
          foreground: "#FFFFFF",
        },
        border: "#1C1D22",
        input: "#121317",
        ring: "#CC9166",
      },
      borderRadius: {
        card: "10px",
        pill: "9999px",
        lg: "10px",
        md: "8px",
        sm: "6px",
      },
    },
  },
  plugins: [],
};

export default config;
