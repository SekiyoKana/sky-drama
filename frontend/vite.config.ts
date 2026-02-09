import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  plugins: [
    vue(),
    tailwindcss(),
  ],
  server: {
    port: 5173,
    proxy: {
      '/v1': {
        target: 'http://127.0.0.1:11451',
        changeOrigin: true
      },
      '/api/health': {
        target: 'http://127.0.0.1:11451',
        changeOrigin: true,
        rewrite: (path) => '/'
      },
      '/api/shutdown': {
        target: 'http://127.0.0.1:11451',
        changeOrigin: true,
        rewrite: (path) => '/shutdown'
      },
      '/api': {
        target: 'http://127.0.0.1:11451',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') // 根据后端是否有 /api 前缀决定是否需要 rewrite
      },
      '/assets': {
        target: 'http://127.0.0.1:11451',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/static/, '') // 根据后端是否有 /static 前缀决定是否需要 rewrite
      },
      // Proxy WebSocket
      '/logs': {
        target: 'http://127.0.0.1:11451',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://127.0.0.1:11451',
        ws: true,
        changeOrigin: true,
      }
    }
  }
})
