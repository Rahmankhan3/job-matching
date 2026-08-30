/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Syne', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      colors: {
        ink: {
          50: '#f0f0f4',
          100: '#e0e0e9',
          200: '#c1c1d3',
          300: '#9393b3',
          400: '#6b6b96',
          500: '#4d4d7a',
          600: '#3d3d62',
          700: '#2d2d4a',
          800: '#1e1e32',
          900: '#0f0f1a',
          950: '#080810',
        },
        acid: {
          50: '#f0fff4',
          100: '#dcffe8',
          200: '#a8ffc4',
          300: '#6cffa0',
          400: '#2dff76',
          500: '#00e55a',
          600: '#00b846',
          700: '#008a33',
          800: '#005c22',
          900: '#002e11',
        },
        amber: {
          400: '#fbbf24',
          500: '#f59e0b',
        }
      },
      animation: {
        'fade-up': 'fadeUp 0.6s ease forwards',
        'fade-in': 'fadeIn 0.4s ease forwards',
        'slide-right': 'slideRight 0.5s ease forwards',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
