import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../app/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/ingest': 'http://localhost:8000',
      '/graph': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
