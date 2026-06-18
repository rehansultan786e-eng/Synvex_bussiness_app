// tailwind.config.js
//
// Design tokens for the Synvex Business Management System.
// Palette matches the Synvex logo: deep charcoal/black background accents
// paired with a vivid purple/violet primary, on a clean white base.

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#6D28D9',   // Synvex violet — primary brand color
          dark: '#5B21B6',
          light: '#8B5CF6',     // lighter violet — accent / hover states
        },
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F7F6FB',    // soft lavender-tinted gray section background
        },
        status: {
          pending: '#B45309',
          approved: '#15803D',
          overdue: '#B91C1C',
          paid: '#1D4ED8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '14px',
        control: '10px',
      },
      boxShadow: {
        soft: '0 1px 2px rgba(16, 24, 40, 0.04), 0 2px 8px rgba(16, 24, 40, 0.06)',
        elevated: '0 4px 12px rgba(16, 24, 40, 0.08), 0 2px 4px rgba(16, 24, 40, 0.04)',
      },
    },
  },
  plugins: [],
}