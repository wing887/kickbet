/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        kb: {
          bg: '#08090a',
          'bg-card': 'rgba(255, 255, 255, 0.03)',
          'bg-secondary': 'rgba(255, 255, 255, 0.05)',
          border: 'rgba(255, 255, 255, 0.1)',
          'border-hover': 'rgba(99, 102, 241, 0.3)',
          accent: '#6366f1',
          'accent-hover': '#4f46e5',
          text: {
            primary: '#ffffff',
            secondary: 'rgba(255, 255, 255, 0.7)',
            muted: 'rgba(255, 255, 255, 0.5)',
          },
          success: '#22c55e',
          warning: '#f59e0b',
          danger: '#ef4444',
        },
      },
      fontFamily: {
        kb: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '0.75rem',
        button: '0.5rem',
      },
      backdropBlur: {
        card: '12px',
      },
    },
  },
  plugins: [],
}