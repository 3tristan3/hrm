// vite.config 文件，实现对应模块能力。
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath } from "node:url";

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      input: {
        main: fileURLToPath(new URL("./index.html", import.meta.url)),
        qr: fileURLToPath(new URL("./qr.html", import.meta.url)),
      },
    },
  },
  server: {
    port: 8080,
  },
});

