/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/js/**/*.js',
    './static/src/**/*.html',
    './**/*.py',
  ],
  safelist: [
    'bg-rose-50', 'bg-rose-600', 'text-rose-800', 'text-rose-700',
    'bg-sky-50', 'bg-sky-600', 'text-sky-800', 'text-sky-700',
    'bg-emerald-50', 'bg-emerald-600', 'text-emerald-800', 'text-emerald-700',
    'bg-indigo-50', 'bg-indigo-600', 'text-indigo-800', 'text-indigo-700',
    'bg-orange-50', 'bg-orange-600', 'text-orange-800', 'text-orange-700',
    'bg-amber-50', 'bg-amber-600', 'text-amber-800', 'text-amber-700',
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
