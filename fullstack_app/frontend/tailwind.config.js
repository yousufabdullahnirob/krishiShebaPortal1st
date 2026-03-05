/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f1f8ed",
          100: "#ddeed4",
          200: "#bddfaa",
          300: "#94c975",
          400: "#71af4f",
          500: "#539235",
          600: "#3f7528",
          700: "#325d22",
          800: "#2b4a1f",
          900: "#253f1d",
          950: "#11220c",
        },
      },
    },
  },
  plugins: [],
};
