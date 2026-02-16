// Vite 构建配置：用于应聘端开发调试、别名解析与打包行为。
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

