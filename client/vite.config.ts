import tailwindcss from "@tailwindcss/vite"
import react from '@vitejs/plugin-react'
import path from "path"
import { visualizer } from 'rollup-plugin-visualizer'
import { fileURLToPath } from 'url'
import { defineConfig, Plugin } from 'vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react({
      jsxRuntime: 'automatic' // Modern JSX transform for React 18
    }),
    visualizer({
      filename: 'dist/stats.html',
      open: false
    }) as Plugin,
    tailwindcss()
  ],
  publicDir: 'public',
  define: {
    global: 'globalThis',
  },
  resolve: {
    alias: {
      buffer: 'buffer',
      stream: 'stream-browserify',
      assert: 'assert',
      "@": path.resolve(__dirname, "./src"),
    }
  },
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