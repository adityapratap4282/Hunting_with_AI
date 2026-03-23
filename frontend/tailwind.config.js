/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        panel: '#111827',
        panelAlt: '#1f2937',
        accent: '#2563eb',
      },
    },
  },
  plugins: [],
}
