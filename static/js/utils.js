/**
 * Utilidades JavaScript globales para el proyecto KenkoMed
 */

/**
 * Formatea un RUT chileno agregando puntos y guión (versión mejorada sin saltos de cursor)
 * @param {HTMLInputElement} input - El elemento input que contiene el RUT
 */
function formatoRUT(input) {
    const cursorPosition = input.selectionStart;
    const oldValue = input.value;
    
    let value = input.value.replace(/[^0-9Kk]/g, '');
    
    if (value.length > 1) {
        value = value.slice(0, -1).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + '-' + value.slice(-1);
    }
    
    input.value = value;
    
    // Restaurar posición del cursor ajustada
    const newPosition = cursorPosition + (value.length - oldValue.length);
    input.setSelectionRange(newPosition, newPosition);
}

/**
 * Formatea un RUT solo al salir del campo (versión onBlur)
 * @param {HTMLInputElement} input - El elemento input que contiene el RUT
 */
function formatoRUTOnBlur(input) {
    let value = input.value.replace(/[^0-9Kk]/g, '');
    
    if (value.length > 1) {
        value = value.slice(0, -1).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + '-' + value.slice(-1);
    }
    
    input.value = value;
}

/**
 * Limpia formato del RUT para permitir escritura libre
 * @param {HTMLInputElement} input - El elemento input que contiene el RUT
 */
function limpiarFormatoRUT(input) {
    // Solo permite números y K/k, sin formato
    const cursorPosition = input.selectionStart;
    const oldValue = input.value;
    
    let value = input.value.replace(/[^0-9Kk]/g, '');
    input.value = value;
    
    // Mantener posición del cursor
    const newPosition = cursorPosition + (value.length - oldValue.length);
    input.setSelectionRange(newPosition, newPosition);
}

/**
 * Valida si un RUT chileno es válido
 * @param {string} rut - El RUT a validar (con o sin formato)
 * @returns {boolean} - True si el RUT es válido, false si no
 */
function validarRUT(rut) {
    // Limpiar el RUT
    rut = rut.replace(/[^0-9Kk]/g, '').toUpperCase();
    
    if (rut.length < 2) return false;
    
    const cuerpo = rut.slice(0, -1);
    const dv = rut.slice(-1);
    
    // Calcular dígito verificador
    let suma = 0;
    let multiplo = 2;
    
    for (let i = cuerpo.length - 1; i >= 0; i--) {
        suma += parseInt(cuerpo[i]) * multiplo;
        multiplo = multiplo === 7 ? 2 : multiplo + 1;
    }
    
    const dvCalculado = 11 - (suma % 11);
    const dvEsperado = dvCalculado === 11 ? '0' : dvCalculado === 10 ? 'K' : dvCalculado.toString();
    
    return dv === dvEsperado;
}

/**
 * Limpia un RUT quitando puntos y guión
 * @param {string} rut - El RUT a limpiar
 * @returns {string} - RUT limpio
 */
function limpiarRUT(rut) {
    return rut.replace(/[^0-9Kk]/g, '');
}

/**
 * Configuración de comportamiento del RUT
 */
const RUT_CONFIG = {
    formatoTiempoReal: true, // Cambiar a false para formato solo onBlur
    validacionTiempoReal: false, // true para validar mientras escribe
    mostrarErrores: true
};

/**
 * Aplica el formato de RUT según la configuración
 */
function inicializarFormatoRUT() {
    const inputs = document.querySelectorAll('.rut-input');
    
    inputs.forEach(input => {
        // Remover listeners existentes
        input.removeEventListener('input', handleRutInput);
        input.removeEventListener('blur', handleRutBlur);
        input.removeEventListener('focus', handleRutFocus);
        
        if (RUT_CONFIG.formatoTiempoReal) {
            // OPCIÓN 1: Formato en tiempo real (recomendado)
            input.addEventListener('input', handleRutInput);
        } else {
            // OPCIÓN 2: Formato solo al salir del campo
            input.addEventListener('input', handleRutInputSimple);
            input.addEventListener('focus', handleRutFocus);
        }
        
        // Siempre validar al salir del campo
        input.addEventListener('blur', handleRutBlur);
    });
}

// Event handlers
function handleRutInput(event) {
    formatoRUT(event.target);
    
    if (RUT_CONFIG.validacionTiempoReal) {
        validarRutVisualmente(event.target);
    }
}

function handleRutInputSimple(event) {
    // Solo limpia caracteres inválidos, sin formatear
    limpiarFormatoRUT(event.target);
}

function handleRutFocus(event) {
    // Al entrar al campo, mostrar sin formato para edición libre
    if (!RUT_CONFIG.formatoTiempoReal) {
        const input = event.target;
        input.value = limpiarRUT(input.value);
    }
}

function handleRutBlur(event) {
    const input = event.target;
    
    // Formatear al salir del campo
    if (!RUT_CONFIG.formatoTiempoReal) {
        formatoRUTOnBlur(input);
    }
    
    // Validar siempre al salir
    validarRutVisualmente(input);
}

function validarRutVisualmente(input) {
    const rutLimpio = limpiarRUT(input.value);
    
    if (rutLimpio.length > 1 && !validarRUT(rutLimpio)) {
        input.classList.add('border-red-500', 'is-invalid');
        input.classList.remove('border-gray-300', 'is-valid');
        
        if (RUT_CONFIG.mostrarErrores) {
            mostrarErrorRut(input, 'RUT inválido');
        }
    } else if (rutLimpio.length > 1) {
        input.classList.remove('border-red-500', 'is-invalid');
        input.classList.add('border-gray-300', 'is-valid');
        
        ocultarErrorRut(input);
    } else {
        // RUT muy corto, limpiar estilos
        input.classList.remove('border-red-500', 'is-invalid', 'is-valid');
        input.classList.add('border-gray-300');
        ocultarErrorRut(input);
    }
}

function mostrarErrorRut(input, mensaje) {
    let errorMsg = input.parentNode.querySelector('.rut-error');
    if (!errorMsg) {
        errorMsg = input.nextElementSibling;
        if (errorMsg && errorMsg.id === 'mensaje-error') {
            errorMsg.style.display = 'block';
            errorMsg.textContent = mensaje;
        }
    } else {
        errorMsg.textContent = mensaje;
        errorMsg.classList.remove('hidden');
    }
}

function ocultarErrorRut(input) {
    let errorMsg = input.parentNode.querySelector('.rut-error');
    if (!errorMsg) {
        errorMsg = input.nextElementSibling;
        if (errorMsg && errorMsg.id === 'mensaje-error') {
            errorMsg.style.display = 'none';
        }
    } else {
        errorMsg.classList.add('hidden');
    }
}

/**
 * Función para cambiar el comportamiento del RUT dinámicamente
 * @param {Object} config - Nueva configuración
 */
function configurarRUT(config) {
    Object.assign(RUT_CONFIG, config);
    inicializarFormatoRUT(); // Reinicializar con nueva configuración
}

/**
 * Función para mostrar/ocultar contraseña
 * @param {string} passwordInputId - ID del input de contraseña
 * @param {string} toggleButtonId - ID del botón para alternar
 */
function setupPasswordToggle(passwordInputId, toggleButtonId) {
    const passwordInput = document.getElementById(passwordInputId);
    const toggleButton = document.getElementById(toggleButtonId);
    
    if (!passwordInput || !toggleButton) return;
    
    const eyeIcon = toggleButton.querySelector('svg');
    
    toggleButton.addEventListener('click', function() {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            if (eyeIcon) {
                eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.477 0-8.268-2.943-9.542-7a9.956 9.956 0 012.223-3.592m3.62-2.956A9.953 9.953 0 0112 5c4.477 0 8.268 2.943 9.542 7a9.96 9.96 0 01-4.293 5.368M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />`;
            }
        } else {
            passwordInput.type = 'password';
            if (eyeIcon) {
                eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />`;
            }
        }
    });
}

// Inicializar cuando el DOM esté listo (compatible con jQuery y vanilla JS)
function initializeUtils() {
    inicializarFormatoRUT();
}

// Compatibilidad con jQuery y vanilla JavaScript
if (typeof jQuery !== 'undefined') {
    $(document).ready(function() {
        initializeUtils();
    });
} else {
    document.addEventListener('DOMContentLoaded', function() {
        initializeUtils();
    });
}

// Para permitir inicialización manual y configuración
window.initializeKenkomedUtils = initializeUtils;
window.configurarRUT = configurarRUT;
window.RUT_CONFIG = RUT_CONFIG;
