/**
 * ============================================================================
 * UTILIDADES JAVASCRIPT GLOBALES PARA EL PROYECTO KENKOMED
 * ============================================================================
 * 
 * Este archivo contiene todas las funciones JavaScript reutilizables del proyecto.
 * Está organizado en las siguientes secciones:
 * 
 * 1. VALIDACIÓN Y FORMATEO DE RUT CHILENO
 * 2. SISTEMA DE CONFIGURACIÓN DE RUT
 * 3. FUNCIONES DE COMPATIBILIDAD LEGACY
 * 4. UTILIDADES DE INTERFAZ DE USUARIO
 * 5. INICIALIZACIÓN Y CONFIGURACIÓN GLOBAL
 */

// ============================================================================
// 1. VALIDACIÓN Y FORMATEO DE RUT CHILENO
// ============================================================================
// Esta sección contiene todas las funciones relacionadas con la validación
// y formateo de RUTs chilenos. Incluye tanto versiones modernas como legacy.

/**
 * Valida si un RUT chileno es válido usando el algoritmo del dígito verificador
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
 * Limpia un RUT quitando todos los caracteres que no sean números o K/k
 * @param {string} rut - El RUT a limpiar
 * @returns {string} - RUT limpio (solo números y K/k)
 */
function limpiarRUT(rut) {
    return rut.replace(/[^0-9Kk]/g, '');
}

/**
 * Formatea un RUT chileno agregando puntos y guión (versión para elementos input)
 * Mantiene la posición del cursor para una mejor experiencia de usuario
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
 * Formatea un RUT solo al salir del campo (versión onBlur para elementos input)
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
 * Formatea un RUT chileno con puntos y guión (versión para strings)
 * Útil para formatear RUTs sin afectar elementos DOM
 * @param {string} rut - RUT sin formato o parcialmente formateado
 * @return {string} RUT formateado (ej: "12.345.678-9")
 */
function formatearRutString(rut) {
    // Eliminar caracteres no válidos
    let rutLimpio = rut.replace(/[^0-9Kk]/g, '');
    
    if (rutLimpio.length > 1) {
        // Separar cuerpo y dígito verificador
        let cuerpo = rutLimpio.slice(0, -1);
        let dv = rutLimpio.slice(-1);
        
        // Formatear el cuerpo con puntos
        cuerpo = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        
        return cuerpo + '-' + dv;
    }
    
    return rutLimpio;
}

/**
 * Limpia formato del RUT para permitir escritura libre
 * Mantiene la posición del cursor
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

// ============================================================================
// 2. SISTEMA DE CONFIGURACIÓN DE RUT
// ============================================================================
// Sistema moderno y configurable para manejar la validación y formateo de RUTs.
// Permite diferentes comportamientos según las necesidades del formulario.

/**
 * Configuración global del comportamiento del RUT
 * Permite personalizar cómo se comporta la validación y formateo
 */
const RUT_CONFIG = {
    formatoTiempoReal: true,        // Si formatea mientras el usuario escribe
    validacionTiempoReal: false     // Si valida mientras el usuario escribe
};

/**
 * Inicializa el sistema moderno de formateo de RUT
 * Busca todos los elementos con clase 'rut-input' y les aplica la configuración
 */
function inicializarFormatoRUT() {
    const inputs = document.querySelectorAll('.rut-input');
    
    inputs.forEach(input => {
        // Evitar listeners duplicados verificando si ya está configurado
        if (input.dataset.rutConfigured) return;
        input.dataset.rutConfigured = 'true';
        
        if (RUT_CONFIG.formatoTiempoReal) {
            // Formato en tiempo real (recomendado)
            input.addEventListener('input', handleRutInput);
        } else {
            // Formato solo al salir del campo
            input.addEventListener('focus', handleRutFocus);
        }
        
        // Siempre validar al salir del campo
        input.addEventListener('blur', handleRutBlur);
    });
}

/**
 * Manejadores de eventos para el sistema moderno de RUT
 */

// Maneja la entrada de texto en tiempo real
function handleRutInput(event) {
    formatoRUT(event.target);
    
    if (RUT_CONFIG.validacionTiempoReal) {
        validarRutVisualmente(event.target);
    }
}

// Maneja cuando el usuario entra al campo
function handleRutFocus(event) {
    if (!RUT_CONFIG.formatoTiempoReal) {
        const input = event.target;
        input.value = limpiarRUT(input.value);
    }
}

// Maneja cuando el usuario sale del campo
function handleRutBlur(event) {
    const input = event.target;
    
    // Formatear al salir del campo
    if (!RUT_CONFIG.formatoTiempoReal) {
        formatoRUTOnBlur(input);
    }
    
    // Validar siempre al salir
    validarRutVisualmente(input);
}

/**
 * Valida visualmente un RUT y aplica estilos CSS correspondientes
 * Muestra iconos de válido/inválido y cambia colores de borde
 * @param {HTMLInputElement} input - El elemento input a validar
 */
function validarRutVisualmente(input) {
    const rutLimpio = limpiarRUT(input.value);
    
    if (rutLimpio.length > 1 && !validarRUT(rutLimpio)) {
        // RUT inválido: aplicar estilos de error
        input.classList.add('border-red-500', 'is-invalid');
        input.style.backgroundImage = 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 12 12\' width=\'12\' height=\'12\' fill=\'none\' stroke=\'%23dc3545\'%3e%3ccircle cx=\'6\' cy=\'6\' r=\'4.5\'/%3e%3cpath stroke-linejoin=\'round\' d=\'M5.8 3.6h.4L6 6.5z\'/%3e%3ccircle cx=\'6\' cy=\'8.2\' r=\'.6\' fill=\'%23dc3545\' stroke=\'none\'/%3e%3c/svg%3e")';
        input.style.backgroundRepeat = 'no-repeat';
        input.style.backgroundPosition = 'right calc(.375em + .1875rem) center';
        input.style.backgroundSize = 'calc(.75em + .375rem) calc(.75em + .375rem)';
        input.classList.remove('border-gray-300', 'is-valid');
    } else if (rutLimpio.length > 1) {
        // RUT válido: aplicar estilos de éxito
        input.classList.remove('border-red-500', 'is-invalid');
        input.classList.add('border-gray-300', 'is-valid');
        input.style.backgroundImage = 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 8 8\'%3e%3cpath fill=\'%23198754\' d=\'M2.3 6.73.6 4.53c-.4-1.04.46-1.4 1.1-.8l1.1 1.4 3.4-3.8c.6-.63 1.6-.27 1.2.7l-4 4.6c-.43.5-.8.4-1.1.1z\'/%3e%3c/svg%3e")';
        input.style.backgroundRepeat = 'no-repeat';
        input.style.backgroundPosition = 'right calc(.375em + .1875rem) center';
        input.style.backgroundSize = 'calc(.75em + .375rem) calc(.75em + .375rem)';
    } else {
        // RUT muy corto: limpiar estilos
        input.classList.remove('border-red-500', 'is-invalid', 'is-valid');
        input.classList.add('border-gray-300');
        input.style.backgroundImage = 'none';
    }
}

/**
 * Función para cambiar la configuración del RUT dinámicamente
 * @param {Object} config - Nueva configuración a aplicar
 */
function configurarRUT(config) {
    Object.assign(RUT_CONFIG, config);
    inicializarFormatoRUT(); // Reinicializar con nueva configuración
}

// ============================================================================
// 3. FUNCIONES DE COMPATIBILIDAD LEGACY
// ============================================================================
// Funciones para mantener compatibilidad con código existente que usa
// patrones antiguos de validación de RUT. Se mantienen por retrocompatibilidad.

/**
 * Maneja el evento de entrada de texto en el campo RUT (versión legacy)
 * Compatible con código existente que busca elementos por ID específicos
 */
function manejarRutLegacy(rutInput = null, mensajeError = null) {
    // Si no se pasan elementos, buscarlos por ID
    if (!rutInput) rutInput = document.getElementById("rut");
    if (!mensajeError) mensajeError = document.getElementById("mensaje-error");
    
    if (!rutInput) return;
    
    // Usar las funciones modernas para evitar duplicación
    formatoRUT(rutInput);
    
    if (validarRUT(rutInput.value)) {
        if (mensajeError) mensajeError.style.display = "none";
        rutInput.classList.remove('border-red-500');
        rutInput.classList.add('border-green-500');
    } else {
        if (mensajeError) mensajeError.style.display = "block";
        rutInput.classList.remove('border-green-500');
        rutInput.classList.add('border-red-500');
    }
}

/**
 * Maneja el evento de pérdida de foco en el campo RUT (versión legacy)
 */
function onBlurRutLegacy(rutInput = null, mensajeError = null) {
    // Si no se pasan elementos, buscarlos por ID
    if (!rutInput) rutInput = document.getElementById("rut");
    if (!mensajeError) mensajeError = document.getElementById("mensaje-error");
    
    if (!rutInput) return;
    
    // Usar las funciones modernas
    if (!RUT_CONFIG.formatoTiempoReal) {
        formatoRUTOnBlur(rutInput);
    }
    
    if (validarRUT(rutInput.value)) {
        if (mensajeError) mensajeError.style.display = "none";
        rutInput.classList.remove('border-red-500');
        rutInput.classList.add('border-green-500');
    } else {
        if (mensajeError) mensajeError.style.display = "block";
        rutInput.classList.remove('border-green-500');
        rutInput.classList.add('border-red-500');
    }
}

/**
 * Inicializa la validación legacy de RUT para compatibilidad con código existente
 * Útil para formularios que usan IDs específicos predefinidos
 * @param {string} rutInputId - ID del input del RUT (por defecto "rut")
 * @param {string} mensajeErrorId - ID del mensaje de error (por defecto "mensaje-error")
 */
function inicializarValidacionRutLegacy(rutInputId = "rut", mensajeErrorId = "mensaje-error") {
    const rutInput = document.getElementById(rutInputId);
    const mensajeError = document.getElementById(mensajeErrorId);
    
    if (rutInput) {
        rutInput.addEventListener("blur", () => onBlurRutLegacy(rutInput, mensajeError));
        rutInput.addEventListener("input", () => manejarRutLegacy(rutInput, mensajeError));
    }
}

// ============================================================================
// 4. UTILIDADES DE INTERFAZ DE USUARIO
// ============================================================================
// Funciones auxiliares para mejorar la experiencia del usuario en formularios
// y componentes de la interfaz.

/**
 * Configurar funcionalidad de mostrar/ocultar contraseña
 * Permite al usuario alternar entre ver y ocultar el texto de la contraseña
 * @param {string} passwordInputId - ID del input de contraseña
 * @param {string} toggleButtonId - ID del botón para alternar visibilidad
 */
function setupPasswordToggle(passwordInputId, toggleButtonId) {
    const passwordInput = document.getElementById(passwordInputId);
    const toggleButton = document.getElementById(toggleButtonId);
    
    if (!passwordInput || !toggleButton) return;
    
    const eyeIcon = toggleButton.querySelector('svg');
    
    toggleButton.addEventListener('click', function() {
        if (passwordInput.type === 'password') {
            // Mostrar contraseña
            passwordInput.type = 'text';
            if (eyeIcon) {
                // Cambiar a icono de "ojo tachado"
                eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.477 0-8.268-2.943-9.542-7a9.956 9.956 0 012.223-3.592m3.62-2.956A9.953 9.953 0 0112 5c4.477 0 8.268 2.943 9.542 7a9.96 9.96 0 01-4.293 5.368M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />`;
            }
        } else {
            // Ocultar contraseña
            passwordInput.type = 'password';
            if (eyeIcon) {
                // Cambiar a icono de "ojo normal"
                eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />`;
            }
        }
    });
}

// ============================================================================
// 5. INICIALIZACIÓN Y CONFIGURACIÓN GLOBAL
// ============================================================================
// Sistema de inicialización que se ejecuta automáticamente cuando se carga
// la página. Configura todos los componentes y funcionalidades.

/**
 * Función principal de inicialización
 * Se ejecuta automáticamente cuando el DOM está listo
 * Inicializa todos los sistemas: RUT moderno, RUT legacy, etc.
 */
function initializeUtils() {
    // Inicializar sistema moderno de RUT
    inicializarFormatoRUT();
    
    // Inicializar sistema legacy para compatibilidad con código existente
    inicializarValidacionRutLegacy();
}

// ============================================================================
// CONFIGURACIÓN DE AUTO-INICIALIZACIÓN
// ============================================================================
// El sistema se inicializa automáticamente tanto con jQuery como con vanilla JavaScript

// Compatibilidad con jQuery (si está disponible)
if (typeof jQuery !== 'undefined') {
    $(document).ready(function() {
        initializeUtils();
    });
} else {
    // Vanilla JavaScript
    document.addEventListener('DOMContentLoaded', function() {
        initializeUtils();
    });
}

// ============================================================================
// EXPOSICIÓN GLOBAL DE FUNCIONES
// ============================================================================
// Hace las funciones principales disponibles globalmente para uso en otros scripts

// Funciones principales del sistema
window.initializeKenkomedUtils = initializeUtils;
window.configurarRUT = configurarRUT;
window.RUT_CONFIG = RUT_CONFIG;

// Funciones de validación y formateo
window.validarRUT = validarRUT;
window.formatearRutString = formatearRutString;
window.limpiarRUT = limpiarRUT;

// Funciones legacy para compatibilidad
window.manejarRutLegacy = manejarRutLegacy;
window.onBlurRutLegacy = onBlurRutLegacy;
window.inicializarValidacionRutLegacy = inicializarValidacionRutLegacy;

// Utilidades de UI
window.setupPasswordToggle = setupPasswordToggle;
