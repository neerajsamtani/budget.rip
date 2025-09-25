import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'automatic' // Modern JSX transform for React 18
    }),
    visualizer({
      filename: 'dist/stats.html',
      open: false
    }) as any
  ],
  publicDir: 'public',
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          plotly: ['plotly.js', 'react-plotly.js']
        }
      }
    }
  },
  server: {
    host: 'dev.localhost'
  }
})