/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#137fec',
        'dark-bg': '#101922',
        'light-bg': '#f6f7f8',
      },
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
      },
      backdropBlur: {
        'glass': '24px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
