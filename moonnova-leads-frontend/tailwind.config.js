/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F5F2EA",
        backgroundSoft: "#FBFAF7",
        card: "#FFFFFF",
        cardSoft: "#F9F7F0",
        sidebar: "#12110F",
        sidebarSoft: "#1D1A16",
        primary: "#B7791F",
        primaryDark: "#92400E",
        primarySoft: "#FFF7ED",
        accent: "#0F766E",
        accentSoft: "#ECFDF5",
        borderSoft: "#E4DDCF",
        mutedText: "#64748B",
        success: "#15803D",
        successSoft: "#DCFCE7",
        warning: "#B45309",
        warningSoft: "#FEF3C7",
        danger: "#B91C1C",
        dangerSoft: "#FEE2E2"
      },
      boxShadow: {
        soft: "0 18px 48px rgba(17, 24, 39, 0.08)",
        card: "0 22px 60px rgba(17, 24, 39, 0.10)",
        glow: "0 16px 34px rgba(183, 121, 31, 0.22)"
      }
    }
  },
  plugins: []
};
