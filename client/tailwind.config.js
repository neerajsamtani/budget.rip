/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Nordic Color System - semantic naming
        primary: {
          DEFAULT: 'var(--color-nordic-blue)',
          light: 'var(--color-light-nordic-blue)',
          dark: 'var(--color-deep-nordic-blue)',
        },
        neutral: {
          50: 'var(--color-white)',
          100: 'var(--color-soft-white)',
          200: 'var(--color-light-gray)',
          300: 'var(--color-medium-gray)',
          500: 'var(--color-dark-gray)',
          700: 'var(--color-charcoal)',
          900: 'var(--color-deep-charcoal)',
        },
        semantic: {
          success: 'var(--color-success)',
          'success-light': 'var(--color-success-light)',
          warning: 'var(--color-warning)',
          'warning-light': 'var(--color-warning-light)',
          error: 'var(--color-error)',
          'error-light': 'var(--color-error-light)',
          neutral: 'var(--color-neutral)',
          progress: 'var(--color-progress)',
        },

        // Tailwind Design System mappings
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        card: {
          DEFAULT: 'var(--card)',
          foreground: 'var(--card-foreground)',
        },
        popover: {
          DEFAULT: 'var(--popover)',
          foreground: 'var(--popover-foreground)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          foreground: 'var(--muted-foreground)',
        },
        accent: {
          DEFAULT: 'var(--accent)',
          foreground: 'var(--accent-foreground)',
        },
        destructive: {
          DEFAULT: 'var(--destructive)',
          foreground: 'var(--destructive-foreground)',
        },
        border: 'var(--border)',
        input: 'var(--input)',
        ring: 'var(--ring)',
        chart: {
          1: 'var(--chart-1)',
          2: 'var(--chart-2)',
          3: 'var(--chart-3)',
          4: 'var(--chart-4)',
          5: 'var(--chart-5)',
        },
      },
      fontFamily: {
        // Semantic font names
        'heading': ['var(--font-inter)'],
        'body': ['var(--font-source-sans)'],

        // Direct font names (for backward compatibility)
        'inter': ['var(--font-inter)'],
        'source-sans': ['var(--font-source-sans)'],

        // Design system defaults
        'sans': ['var(--font-source-sans)'],
        'display': ['var(--font-inter)'],
      },
      borderRadius: {
        'sm': 'var(--radius-sm)',
        'md': 'var(--radius-md)',
        'lg': 'var(--radius-lg)',
        'xl': 'var(--radius-xl)',
      },
    },
  },
  plugins: [],
};