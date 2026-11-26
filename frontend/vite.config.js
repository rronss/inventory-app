import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The browser only ever talks to its own origin; /api is forwarded to the backend, so no CORS settings are needed.
export default defineConfig({
  plugins: [react()],
  server: { port: 5180, proxy: { '/api': 'http://localhost:8100' } },
})
