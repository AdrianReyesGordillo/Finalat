/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f0f0fa',
          100: '#e0e0f0',
          200: '#c4c3e0',
          300: '#9b99c8',
          400: '#6e6bab',
          500: '#4a4790',
          600: '#3a3878',
          700: '#2D2B6B',
          800: '#242258',
          900: '#1a1945',
        },
        accent: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#F0A500',
          500: '#F0A500',
          600: '#d49200',
          700: '#a87300',
        },
        surface: {
          50: '#FAFAFE',
          100: '#F5F5FA',
          200: '#E0E0F0',
        }
      }
    },
  },
  plugins: [],
}
