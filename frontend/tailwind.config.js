/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        eco: {
          dark: '#064e3b', // Deep Emerald Green
          primary: '#059669', // Emerald primary
          light: '#34d399', // Fresh Green
          accent: '#f59e0b', // Warm Amber
          background: '#f8fafc', // Off-white neutral
          surface: '#ffffff',
          text: '#1e293b', // Dark charcoal
        }
      }
    },
  },
  plugins: [],
}
