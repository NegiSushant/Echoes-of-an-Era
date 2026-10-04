/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        capsule: {
          bg: "#0d0f12",
          card: "#161a22",
          border: "#262c38",
          amber: "#d97706",
          gold: "#f59e0b",
          lightGold: "#fef3c7",
          parchment: "#f8f5ee",
          muted: "#94a3b8"
        }
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
