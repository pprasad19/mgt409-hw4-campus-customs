import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The FastAPI backend runs on :8000. Proxying /api and /static keeps the
// frontend on a single origin in dev, so product image paths from the
// database work as-is.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
