// tailwind.config.js
//
// Design tokens for the Synvex Business Management System.
// Style direction: Apple + Stripe + Notion hybrid — clean white base,
// soft navy primary, subtle shadows, rounded corners, minimal clutter.

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1B3A6B',   // Soft Navy Blue — primary brand color
          dark: '#15305a',
          light: '#2E5BA8',     // Professional Blue — accent / hover states
        },
        surface: {
          DEFAULT: '#FFFFFF',
          subtle: '#F7F9FC',    // soft gray section background
        },
        status: {
          pending: '#B45309',   // amber-ish text on amber-50 bg
          approved: '#15803D',  // green
          overdue: '#B91C1C',   // red
          paid: '#1D4ED8',      // blue
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