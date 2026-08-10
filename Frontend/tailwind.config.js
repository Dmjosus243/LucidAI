/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: "#0A1628",
        dark2: "#0D1B33",
        "dark-card": "#111F33",
        "dark-hover": "#16283F",
        cyan: {
          200: "#B5F3FF",
          300: "#7FE7FF",
          400: "#38E1FF",
          500: "#00D4FF",
          600: "#00A8CC",
          700: "#008099",
          DEFAULT: "#00D4FF",
        },
        danger: "#FF4D4D",
        success: "#00C853",
        warning: "#FBBF24",
        primary: {
          50: "#E6F9FF",
          100: "#CCF3FF",
          400: "#38E1FF",
          500: "#00D4FF",
          600: "#00A8CC",
        },
        surface: "#0F1E36",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(0, 212, 255, 0.18)",
        "glow-lg": "0 0 48px rgba(0, 212, 255, 0.22)",
        card: "0 8px 30px rgba(0, 0, 0, 0.35)",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        fadeIn: "fadeIn 0.4s ease-out",
        float: "float 6s ease-in-out infinite",
        pulseGlow: "pulseGlow 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
