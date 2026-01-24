export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class', 
  theme: {
    extend: {
      colors: {
        background: {
          primary: '#0f172a',   // Slate 900 (Fundo principal dark)
          secondary: '#1e293b', // Slate 800 (Cards dark)
          tertiary: '#334155',  // Slate 700 (Bordas/Hovers)
        },
        text: {
          primary: '#f8fafc',   // Slate 50
          secondary: '#cbd5e1', // Slate 300
          tertiary: '#94a3b8',  // Slate 400
        },
        accent: {
          primary: '#3b82f6',   // Blue 500 (Botões, Destaques)
          secondary: '#60a5fa', // Blue 400 (Textos de destaque)
        },
        status: {
          success: '#22c55e',   // Green 500
          warning: '#eab308',   // Yellow 500
          danger: '#ef4444',    // Red 500
        }
      },
      animation: {
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}
