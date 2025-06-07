import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import ElementPlus from 'unplugin-element-plus/vite'
import { px2viewport } from '@mistjs/vite-plugin-px2viewport';

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    px2viewport({
      viewportWidth: 1360,
      unitPrecision: 10,
    }),
    vue(),
    vueDevTools(),
    ElementPlus({}),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
