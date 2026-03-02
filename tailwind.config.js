/** @type {import('tailwindcss').Config} */
module.exports = {
  // Scan ALL Django templates for Tailwind classes
  content: [
    './enrollment_app/templates/**/*.html',
    './admin_app/templates/**/*.html',
    './coordinator_app/templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        primary:          "#991b1b",
        "primary-dark":   "#7f1d1d",
        secondary:        "#eab308",
        "secondary-dark": "#ca8a04",
        accent:           "#b91c1c",
        "ai-primary":     "#10b981",
        "ai-dark":        "#059669",
        coordinator:      "#991b1b",
        "coordinator-dark":"#7f1d1d",
      },
      fontFamily: {
        sans:    ["Poppins", "sans-serif"],
        display: ["Playfair Display", "serif"],
      },
      animation: {
        "fade-in":        "fadeIn       0.3s ease-out",
        "slide-in-right": "slideInRight 0.3s ease-out",
        "modal-fade-in":  "modalFadeIn  0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          from: { transform: "translateX(100%)", opacity: "0" },
          to:   { transform: "translateX(0)",    opacity: "1" },
        },
        modalFadeIn: {
          from: { opacity: "0", transform: "translateY(-20px) scale(0.95)" },
          to:   { opacity: "1", transform: "translateY(0) scale(1)" },
        },
      },
    },
  },
  plugins: [],
};
