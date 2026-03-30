/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // BioCodeTeacher custom colors
        'ct-bg': 'var(--ct-bg)',
        'ct-surface': 'var(--ct-surface)',
        'ct-surface-2': 'var(--ct-surface-2)',
        'ct-border': 'var(--ct-border)',
        'ct-text': 'var(--ct-text)',
        'ct-text-secondary': 'var(--ct-text-secondary)',
        'ct-primary': 'var(--ct-primary)',
        'ct-accent': 'var(--ct-accent)',
        'ct-warm': 'var(--ct-warm)',
        // Explanation section colors
        'ct-purpose': 'var(--ct-purpose)',
        'ct-token': 'var(--ct-token)',
        'ct-param': 'var(--ct-param)',
        'ct-concept': 'var(--ct-concept)',
        // Bio-specific section colors
        'bct-biology': 'var(--bct-biology)',
        'bct-data': 'var(--bct-data)',
        'bct-parameter': 'var(--bct-parameter)',
        'bct-pipeline': 'var(--bct-pipeline)',
        'bct-crosstool': 'var(--bct-crosstool)',
      },
      fontFamily: {
        'sans': ['Plus Jakarta Sans', 'sans-serif'],
        'display': ['Instrument Sans', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
