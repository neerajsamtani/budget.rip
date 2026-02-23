/// <reference types="react-scripts" />

declare module '@tailwindcss/vite' {
  import { Plugin } from 'vite';
  export default function tailwindcss(): Plugin;
}

declare module '@vitejs/plugin-react' {
  import { Plugin } from 'vite';
  interface Options {
    jsxRuntime?: 'automatic' | 'classic';
    [key: string]: unknown;
  }
  export default function react(options?: Options): Plugin;
}
