// vite.config 文件，实现对应模块能力。
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8090,
  },
});

