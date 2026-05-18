/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        outfit: ['Outfit', 'sans-serif'],
        mono:   ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg:      '#0f0f14',
        surface: '#16161f',
        surface2:'#1e1e2e',
        purple:  '#a855f7',
        purpled: '#7c3aed',
        yellow:  '#facc15',
        green:   '#4ade80',
        red:     '#f87171',
        muted:   '#64748b',
      },
      animation: {
        pulse2:  'pulse2 1.2s infinite',
        slideUp: 'slideUp 0.4s ease both',
        shimmer: 'shimmer 1.5s infinite',
        fadeIn:  'fadeIn 0.2s ease both',
      },
      keyframes: {
        pulse2: {
          '0%,100%': { opacity: '1' },
          '50%':     { opacity: '0.4' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          from: { backgroundPosition: '200% 0' },
          to:   { backgroundPosition: '-200% 0' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}