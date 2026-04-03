import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        panel: "#ffffff",
        line: "#dbe3ec",
        muted: "#64748b",
        bg: "#eef3f8",
      },
    },
  },
  plugins: [],
} satisfies Config;
