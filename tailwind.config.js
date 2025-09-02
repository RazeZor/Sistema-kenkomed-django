/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./Login/templates/**/*.{html,js}",
    "./FormularioInicial/templates/**/*.{html,js}",
    "./informe/templates/**/*.{html,js}",
    "./ListaDePacientes/templates/**/*.{html,js}",
    "./menu/templates/**/*.{html,js}",
    "./PanelDeControl/templates/**/*.{html,js}",
    "./PerfilClinico/templates/**/*.{html,js}",
    "./TiposDeFormularios/templates/**/*.{html,js}",
  ],
  theme: {
    extend: {
      keyframes: {
        'fade-in': {
          'from': {
            opacity: '0',
            transform: 'translateY(20px)'
          },
          'to': {
            opacity: '1',
            transform: 'translateY(0)'
          },
        }
      },
      animation: {
        'fade-in': 'fade-in 0.8s ease-out'
      }
    },
  },
  plugins: [],
}
