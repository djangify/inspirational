const typography = require('@tailwindcss/typography')

module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './**/*.py',
  ],
  theme: {
    extend: {},
  },
  plugins: [typography],
}
