/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/js/**/*.js',
    './static/src/**/*.html',
    './**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#227c81',   // Teal-700
        secondary: '#f8fafc', // Slate-50
        accent: '#64748b',    // Slate-500
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
