import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/learnflix/",
  server: {
    port: 5173,
  },
});
