import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  build: {
    outDir: resolve(__dirname, "../custom_components/update_blocklist/www"),
    emptyOutDir: true,
    lib: {
      entry: resolve(__dirname, "src/update-blocklist-panel.ts"),
      formats: ["es"],
      fileName: () => "panel.js",
    },
    rollupOptions: {
      output: { inlineDynamicImports: true },
    },
    sourcemap: false,
    target: "es2022",
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
