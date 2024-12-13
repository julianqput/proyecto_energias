// Importar el archivo JavaScript de typed.js
var script = document.createElement('script');
script.src = 'https://unpkg.com/typed.js@2.1.0/dist/typed.umd.js';

// Esperar a que se cargue typed.js antes de continuar
script.onload = function() {
  // Inicializar Typed para el título
  var typed = new Typed(".auto-type", {
    strings: ["Energía Renovable", "100% Limpia", "La Energía del Futuro"],
    cursorChar: '|',             // Cambia el cursor si prefieres algo más visible
    startDelay: 500,             // Reduce el tiempo de espera inicial
    typeSpeed: 50,               // Ajusta velocidad de tipeo
    backSpeed: 30,               // Ajusta velocidad de borrado
    smartBackspace: true,        // Evita escribir texto ya existente
    loop: true                   // Animación infinita
  });  
};
document.head.appendChild(script);