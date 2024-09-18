/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Add this to scan for class names in your files
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
