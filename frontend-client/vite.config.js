import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api/chat/ws': { target: 'ws://localhost:8000', ws: true },
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
  resolve: {
    alias: {
      '@': '/src',
      '@shared': path.resolve(__dirname, '../shared'),
    },
    dedupe: ['vue', 'element-plus', '@element-plus/icons-vue', 'axios', 'dayjs'],
  },
  test: {
    globals: true,
    environment: 'jsdom',
  },
})
