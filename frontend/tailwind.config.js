/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f5ff',
          100: '#e0eaff',
          200: '#c1d5fe',
          300: '#93b4fd',
          400: '#6090fa',
          500: '#3b6ff6',
          600: '#2457eb',
          700: '#1a44d8',
          800: '#1c38af',
          900: '#1b308a',
          950: '#131f54',
        },
        surface: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
        risk: {
          low:      '#10b981',
          medium:   '#f59e0b',
          high:     '#ef4444',
          critical: '#dc2626',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '0.85rem' }],
      },
      boxShadow: {
        'card':       '0 1px 3px 0 rgb(0 0 0 / 0.04), 0 1px 2px -1px rgb(0 0 0 / 0.04)',
        'card-hover': '0 4px 6px -1px rgb(0 0 0 / 0.06), 0 2px 4px -2px rgb(0 0 0 / 0.04)',
        'elevated':   '0 10px 15px -3px rgb(0 0 0 / 0.06), 0 4px 6px -4px rgb(0 0 0 / 0.04)',
        'modal':      '0 25px 50px -12px rgb(0 0 0 / 0.15)',
        'glow-blue':  '0 0 20px -4px rgb(59 111 246 / 0.25)',
        'inner-ring':  'inset 0 0 0 1px rgb(0 0 0 / 0.04)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.25rem',
      },
      animation: {
        'fade-in':     'fade-in 0.35s ease-out',
        'slide-up':    'slide-up 0.35s ease-out',
        'slide-in':    'slide-in 0.2s ease-out',
        'pulse-ring':  'pulse-ring 2s ease-in-out infinite',
        'shimmer':     'shimmer 2s infinite linear',
        'count-up':    'count-up 0.6s ease-out',
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-up': {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          from: { transform: 'translateX(-100%)' },
          to:   { transform: 'translateX(0)' },
        },
        'pulse-ring': {
          '0%':   { transform: 'scale(0.9)', opacity: '0.7' },
          '50%':  { transform: 'scale(1.1)', opacity: '0' },
          '100%': { transform: 'scale(0.9)', opacity: '0' },
        },
        'shimmer': {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backgroundImage: {
        'shimmer': 'linear-gradient(90deg, transparent 30%, rgba(255,255,255,0.5) 50%, transparent 70%)',
      },
      backgroundSize: {
        'shimmer': '200% 100%',
      },
    },
  },
  plugins: [],
};
