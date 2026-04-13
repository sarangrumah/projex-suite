/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#0F172A",
          blue: "#0A66C2",
          sky: "#0EA5E9",
          50: "#EFF6FF",
          100: "#DBEAFE",
        },
        surface: {
          primary: "#FFFFFF",
          secondary: "#F8FAFC",
          tertiary: "#F1F5F9",
        },
        text: {
          primary: "#1E293B",
          secondary: "#374151",
          muted: "#64748B",
          disabled: "#9CA3AF",
        },
        status: {
          success: "#059669",
          warning: "#D97706",
          error: "#DC2626",
          info: "#0EA5E9",
        },
        priority: {
          critical: "#DC2626",
          high: "#F59E0B",
          normal: "#3B82F6",
          low: "#6B7280",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
