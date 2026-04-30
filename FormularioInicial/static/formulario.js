/**
 * ============================================================================
 * SISTEMA COMPLETO KENKOMED - UTILIDADES Y FORMULARIO DE EVALUACIÓN DE DOLOR
 * ============================================================================
 * 
 * Este archivo contiene todas las funcionalidades JavaScript necesarias para:
 * - Validación y formateo de RUT chileno
 * - Formulario de evaluación de dolor con navegación por secciones
 * - Mapa corporal interactivo
 * - Gestión de campos condicionales
 * 
 * @author v0 & Kenkomed Team
 * @version 3.0 - Unificado
 */

// ============================================================================
// SECCIÓN 1: VALIDACIÓN Y FORMATEO DE RUT CHILENO
// ============================================================================

/**
 * Valida si un RUT chileno es válido usando el algoritmo del dígito verificador
 * @param {string} rut - El RUT a validar (con o sin formato)
 * @returns {boolean} - True si el RUT es válido, false si no
 */
function validarRUT(rut) {
  rut = rut.replace(/[^0-9Kk]/g, "").toUpperCase()

  if (rut.length < 2) return false

  const cuerpo = rut.slice(0, -1)
  const dv = rut.slice(-1)

  let suma = 0
  let multiplo = 2

  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += parseInt(cuerpo[i]) * multiplo
    multiplo = multiplo === 7 ? 2 : multiplo + 1
  }

  const dvCalculado = 11 - (suma % 11)
  const dvEsperado = dvCalculado === 11 ? "0" : dvCalculado === 10 ? "K" : dvCalculado.toString()

  return dv === dvEsperado
}

/**
 * Limpia un RUT quitando todos los caracteres que no sean números o K/k
 * @param {string} rut - El RUT a limpiar
 * @returns {string} - RUT limpio (solo números y K/k)
 */
function limpiarRUT(rut) {
  return rut.replace(/[^0-9Kk]/g, "")
}

/**
 * Formatea un RUT chileno agregando puntos y guión (versión para elementos input)
 * Mantiene la posición del cursor para una mejor experiencia de usuario
 * @param {HTMLInputElement} input - El elemento input que contiene el RUT
 */
function formatoRUT(input) {
  const cursorPosition = input.selectionStart
  const oldValue = input.value

  let value = input.value.replace(/[^0-9Kk]/g, "")

  if (value.length > 1) {
    value = value.slice(0, -1).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "-" + value.slice(-1)
  }

  input.value = value

  const newPosition = cursorPosition + (value.length - oldValue.length)
  input.setSelectionRange(newPosition, newPosition)
}

/**
 * Formatea un RUT solo al salir del campo (versión onBlur para elementos input)
 * @param {HTMLInputElement} input - El elemento input que contiene el RUT
 */
function formatoRUTOnBlur(input) {
  let value = input.value.replace(/[^0-9Kk]/g, "")

  if (value.length > 1) {
    value = value.slice(0, -1).replace(/\B(?=(\d{3})+(?!\d))/g, ".") + "-" + value.slice(-1)
  }

  input.value = value
}

/**
 * Formatea un RUT chileno con puntos y guión (versión para strings)
 * @param {string} rut - RUT sin formato o parcialmente formateado
 * @return {string} RUT formateado (ej: "12.345.678-9")
 */
function formatearRutString(rut) {
  let rutLimpio = rut.replace(/[^0-9Kk]/g, "")

  if (rutLimpio.length > 1) {
    let cuerpo = rutLimpio.slice(0, -1)
    let dv = rutLimpio.slice(-1)
    cuerpo = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".")
    return cuerpo + "-" + dv
  }

  return rutLimpio
}

/**
 * Limpia formato del RUT para permitir escritura libre
 * @param {HTMLInputElement} input - El elemento input que contiene el RUT
 */
function limpiarFormatoRUT(input) {
  const cursorPosition = input.selectionStart
  const oldValue = input.value

  let value = input.value.replace(/[^0-9Kk]/g, "")
  input.value = value

  const newPosition = cursorPosition + (value.length - oldValue.length)
  input.setSelectionRange(newPosition, newPosition)
}

// ============================================================================
// SECCIÓN 2: SISTEMA DE CONFIGURACIÓN DE RUT
// ============================================================================

/**
 * Configuración global del comportamiento del RUT
 */
const RUT_CONFIG = {
  formatoTiempoReal: true,
  validacionTiempoReal: true,
}

/**
 * Inicializa el sistema moderno de formateo de RUT
 */
function inicializarFormatoRUT() {
  const inputs = document.querySelectorAll(".rut-input")

  inputs.forEach((input) => {
    if (input.dataset.rutConfigured) return
    input.dataset.rutConfigured = "true"

    if (RUT_CONFIG.formatoTiempoReal) {
      input.addEventListener("input", handleRutInput)
    } else {
      input.addEventListener("focus", handleRutFocus)
    }

    input.addEventListener("blur", handleRutBlur)
  })
}

/**
 * Manejadores de eventos para el sistema moderno de RUT
 */
function handleRutInput(event) {
  formatoRUT(event.target)

  if (RUT_CONFIG.validacionTiempoReal) {
    validarRutVisualmente(event.target)
  }
}

function handleRutFocus(event) {
  if (!RUT_CONFIG.formatoTiempoReal) {
    const input = event.target
    input.value = limpiarRUT(input.value)
  }
}

function handleRutBlur(event) {
  const input = event.target

  if (!RUT_CONFIG.formatoTiempoReal) {
    formatoRUTOnBlur(input)
  }

  validarRutVisualmente(input)
}

/**
 * Valida visualmente un RUT y aplica estilos CSS correspondientes
 * @param {HTMLInputElement} input - El elemento input a validar
 */
function validarRutVisualmente(input) {
  const rutLimpio = limpiarRUT(input.value)

  if (rutLimpio.length > 1 && !validarRUT(rutLimpio)) {
    input.classList.add("border-red-500", "is-invalid")
    input.classList.remove("border-green-500", "border-gray-300", "is-valid")
  } else if (rutLimpio.length > 1) {
    input.classList.remove("border-red-500", "is-invalid")
    input.classList.add("border-green-500", "is-valid")
    input.classList.remove("border-gray-300")
  } else {
    input.classList.remove("border-red-500", "border-green-500", "is-invalid", "is-valid")
    input.classList.add("border-gray-300")
    input.style.backgroundImage = ""
  }
}

/**
 * Función para cambiar la configuración del RUT dinámicamente
 * @param {Object} config - Nueva configuración a aplicar
 */
function configurarRUT(config) {
  Object.assign(RUT_CONFIG, config)
  inicializarFormatoRUT()
}

// ============================================================================
// SECCIÓN 3: FUNCIONES DE COMPATIBILIDAD LEGACY
// ============================================================================

/**
 * Maneja el evento de entrada de texto en el campo RUT (versión legacy)
 */
function manejarRutLegacy(rutInput = null, mensajeError = null) {
  if (!rutInput) rutInput = document.getElementById("rut")
  if (!mensajeError) mensajeError = document.getElementById("mensaje-error")

  if (!rutInput) return

  formatoRUT(rutInput)

  if (validarRUT(rutInput.value)) {
    if (mensajeError) mensajeError.style.display = "none"
    rutInput.classList.remove("border-red-500")
    rutInput.classList.add("border-green-500")
  } else {
    if (mensajeError) mensajeError.style.display = "block"
    rutInput.classList.remove("border-green-500")
    rutInput.classList.add("border-red-500")
  }
}

/**
 * Maneja el evento de pérdida de foco en el campo RUT (versión legacy)
 */
function onBlurRutLegacy(rutInput = null, mensajeError = null) {
  if (!rutInput) rutInput = document.getElementById("rut")
  if (!mensajeError) mensajeError = document.getElementById("mensaje-error")

  if (!rutInput) return

  if (!RUT_CONFIG.formatoTiempoReal) {
    formatoRUTOnBlur(rutInput)
  }

  if (validarRUT(rutInput.value)) {
    if (mensajeError) mensajeError.style.display = "none"
    rutInput.classList.remove("border-red-500")
    rutInput.classList.add("border-green-500")
  } else {
    if (mensajeError) mensajeError.style.display = "block"
    rutInput.classList.remove("border-green-500")
    rutInput.classList.add("border-red-500")
  }
}

/**
 * Inicializa la validación legacy de RUT
 * @param {string} rutInputId - ID del input del RUT
 * @param {string} mensajeErrorId - ID del mensaje de error
 */
function inicializarValidacionRutLegacy(rutInputId = "rut", mensajeErrorId = "mensaje-error") {
  const rutInput = document.getElementById(rutInputId)
  const mensajeError = document.getElementById(mensajeErrorId)

  if (rutInput) {
    rutInput.addEventListener("blur", () => onBlurRutLegacy(rutInput, mensajeError))
    rutInput.addEventListener("input", () => manejarRutLegacy(rutInput, mensajeError))
  }
}

// ============================================================================
// SECCIÓN 4: FUNCIONES DEL FORMULARIO - UTILIDADES GENERALES
// ============================================================================

/**
 * Maneja el evento de entrada de texto en el campo RUT (wrapper para formulario)
 */
function manejarRut() {
  if (typeof manejarRutLegacy === "function") {
    manejarRutLegacy()
  } else {
    var rutInput = document.getElementById("rut")
    var rut = rutInput.value
    var mensajeError = document.getElementById("mensaje-error")

    if (typeof validarRUT === "function" && validarRUT(rut)) {
      if (typeof formatearRutString === "function") {
        rutInput.value = formatearRutString(rut)
      }
      if (mensajeError) {
        mensajeError.style.display = "none"
      }
      rutInput.classList.remove("border-red-500")
      rutInput.classList.add("border-green-500")
    } else {
      if (mensajeError) {
        mensajeError.style.display = "block"
      }
      rutInput.classList.remove("border-green-500")
      rutInput.classList.add("border-red-500")
    }
  }
}

/**
 * Maneja el evento de pérdida de foco en el campo RUT (wrapper para formulario)
 */
function onBlurRut() {
  if (typeof onBlurRutLegacy === "function") {
    onBlurRutLegacy()
  } else {
    var rutInput = document.getElementById("rut")
    var rut = rutInput.value
    var mensajeError = document.getElementById("mensaje-error")

    if (typeof formatearRutString === "function") {
      rutInput.value = formatearRutString(rut)
    }

    if (typeof validarRUT === "function" && validarRUT(rut)) {
      if (mensajeError) {
        mensajeError.style.display = "none"
      }
      rutInput.classList.remove("border-red-500")
      rutInput.classList.add("border-green-500")
    } else {
      if (mensajeError) {
        mensajeError.style.display = "block"
      }
      rutInput.classList.remove("border-green-500")
      rutInput.classList.add("border-red-500")
    }
  }
}

/**
 * Calcula la fecha de fin de licencia basada en la fecha de inicio y días
 */
function calcularFechaFin() {
  const fechaInicio = document.getElementById("fecha_inicio").value
  const diasLicencia = Number.parseInt(document.getElementById("dias_licencia").value)

  if (fechaInicio && !isNaN(diasLicencia)) {
    const fechaInicioObj = new Date(fechaInicio)
    fechaInicioObj.setDate(fechaInicioObj.getDate() + diasLicencia)

    const fechaFin = fechaInicioObj.toISOString().split("T")[0]
    document.getElementById("fecha_fin").value = fechaFin
  }
}

/**
 * Muestra u oculta el contenedor de calidad de atención según la selección
 */
function toggleCalidadAtencion() {
  const accidenteLaboralSi = document.getElementById("opdolor1")
  const calidadAtencionContainer = document.getElementById("calidadAtencionContainer")

  if (accidenteLaboralSi && calidadAtencionContainer) {
    if (accidenteLaboralSi.checked) {
      calidadAtencionContainer.style.display = "block"
    } else {
      calidadAtencionContainer.style.display = "none"
    }
  }
}

// ============================================================================
// SECCIÓN 5: NAVEGACIÓN POR SECCIONES
// ============================================================================

/**
 * Inicializa el sistema de navegación por secciones
 */
function inicializarNavegacionSecciones() {
  const navButtons = document.querySelectorAll(".nav-section-btn")
  const sections = document.querySelectorAll(".form-section")
  const totalSteps = navButtons.length
  const progressFill = document.getElementById("wizardProgressFill")
  const progressText = document.getElementById("wizardProgressText")
  const stepIndicator = document.getElementById("stepIndicator")
  const btnAnterior = document.getElementById("btnAnterior")
  const btnSiguiente = document.getElementById("btnSiguiente")
  const mobileMenuBtn = document.getElementById("mobileMenuBtn")
  const sidebarOverlay = document.getElementById("sidebarOverlay")
  const sidebar = document.querySelector(".sidebar-nav")

  function getCurrentIndex() {
    let idx = 0
    navButtons.forEach((btn, i) => { if (btn.classList.contains("active")) idx = i })
    return idx
  }

  function goToSection(index) {
    if (index < 0 || index >= totalSteps) return
    const targetBtn = navButtons[index]
    if (targetBtn.disabled) return
    navButtons.forEach(btn => btn.classList.remove("active"))
    targetBtn.classList.add("active")
    targetBtn.classList.add("visited")
    sections.forEach(s => s.classList.remove("active"))
    const sectionId = targetBtn.getAttribute("data-section")
    const targetSection = document.getElementById(sectionId)
    if (targetSection) targetSection.classList.add("active")
    const pct = Math.round(((index + 1) / totalSteps) * 100)
    if (progressFill) progressFill.style.width = pct + "%"
    const label = "Paso " + (index + 1) + " de " + totalSteps
    if (progressText) progressText.textContent = label
    if (stepIndicator) stepIndicator.textContent = label
    if (btnAnterior) btnAnterior.style.visibility = index === 0 ? "hidden" : "visible"
    if (btnSiguiente) {
      if (index === totalSteps - 1) {
        btnSiguiente.innerHTML = '<i class="fas fa-save me-1"></i> Guardar'
        btnSiguiente.onclick = function() { document.getElementById("Step").requestSubmit() }
      } else {
        btnSiguiente.innerHTML = 'Siguiente <i class="fas fa-arrow-right me-1"></i>'
        btnSiguiente.onclick = null
      }
    }
    if (sidebar) sidebar.classList.remove("open")
    if (sidebarOverlay) sidebarOverlay.classList.remove("active")
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  navButtons.forEach((button, i) => {
    button.addEventListener("click", function() { goToSection(i) })
  })
  if (btnAnterior) btnAnterior.addEventListener("click", function() { goToSection(getCurrentIndex() - 1) })
  if (btnSiguiente) btnSiguiente.addEventListener("click", function() { if (getCurrentIndex() < totalSteps - 1) goToSection(getCurrentIndex() + 1) })
  if (mobileMenuBtn && sidebar && sidebarOverlay) {
    mobileMenuBtn.addEventListener("click", function() { sidebar.classList.toggle("open"); sidebarOverlay.classList.toggle("active") })
    sidebarOverlay.addEventListener("click", function() { sidebar.classList.remove("open"); sidebarOverlay.classList.remove("active") })
  }
  goToSection(0)
}

/**
 * Marca una sección como completada
 */
function marcarSeccionCompletada(sectionId) {
  const button = document.querySelector(`[data-section="${sectionId}"]`)
  if (button) {
    button.classList.add("completed")
  }
}

// ============================================================================
// SECCIÓN 6: MAPA CORPORAL Y SELECCIÓN DE PARTES DEL CUERPO
// ============================================================================

/**
 * Definición de las partes del cuerpo para el mapa interactivo
 */
const partesDelCuerpo = [
  // VISTA FRONTAL
  { nombre: "VFCara", x: 42, y: 0, ancho: 34, alto: 51 },
  { nombre: "VFCuello ", x: 29, y: 50, ancho: 52, alto: 20 },
  { nombre: "VFPectoral derecho", x: 23, y: 70, ancho: 35, alto: 39 },
  { nombre: "VFPectoral izquierdo", x: 58, y: 70, ancho: 35, alto: 39 },
  { nombre: "VFHombro derecho", x: 4, y: 70, ancho: 19, alto: 39 },
  { nombre: "VFHombro izquierdo", x: 92, y: 70, ancho: 19, alto: 39 },
  { nombre: "VFBrazo derecho", x: 4, y: 108, ancho: 22, alto: 40 },
  { nombre: "VFBrazo izquierdo", x: 92, y: 108, ancho: 21, alto: 40 },
  { nombre: "VFAntebrazo derecho", x: 1, y: 148, ancho: 24, alto: 60 },
  { nombre: "VFAntebrazo izquierdo", x: 92, y: 148, ancho: 24, alto: 60 },
  { nombre: "VFMano derecha", x: 0, y: 207, ancho: 20, alto: 39 },
  { nombre: "VFMano izquierda", x: 97, y: 207, ancho: 20, alto: 39 },
  { nombre: "VFAbdomen Superior derecho", x: 28, y: 109, ancho: 31, alto: 40 },
  { nombre: "VFAbdomen Superior izquierdo", x: 58, y: 109, ancho: 32, alto: 40 },
  { nombre: "VFAbdomen Inferior derecho", x: 28, y: 149, ancho: 31, alto: 28 },
  { nombre: "VFAbdomen Inferior izquierdo", x: 58, y: 149, ancho: 32, alto: 28 },
  { nombre: "VFPelvis", x: 27, y: 176, ancho: 63, alto: 27 },
  { nombre: "VFGenitales", x: 52, y: 202, ancho: 13, alto: 8 },
  { nombre: "VFMuslo derecho", x: 24, y: 202, ancho: 29, alto: 85 },
  { nombre: "VFMuslo izquierdo", x: 64, y: 202, ancho: 29, alto: 85 },
  { nombre: "VFRodilla derecha", x: 27, y: 287, ancho: 29, alto: 20 },
  { nombre: "VFRodilla izquierda", x: 64, y: 287, ancho: 29, alto: 20 },
  { nombre: "VFPierna derecha", x: 27, y: 307, ancho: 26, alto: 93 },
  { nombre: "VFPierna izquierda", x: 64, y: 307, ancho: 26, alto: 93 },
  { nombre: "VFTalon derecha", x: 29, y: 400, ancho: 24, alto: 12 },
  { nombre: "VFTalon izquierda", x: 64, y: 400, ancho: 26, alto: 12 },
  { nombre: "VFPie derec", x: 29, y: 412, ancho: 24, alto: 37 },
  { nombre: "VFPie izquierdo", x: 64, y: 412, ancho: 26, alto: 37 },
  // VISTA TRASERA
  { nombre: "VTCabeza", x: 211, y: 0, ancho: 34, alto: 51 },
  { nombre: "VTcuello", x: 198, y: 50, ancho: 52, alto: 20 },
  { nombre: "VTEspalda Alta", x: 192, y: 70, ancho: 70, alto: 70 },
  { nombre: "VTHombro izquierdo", x: 173, y: 70, ancho: 19, alto: 39 },
  { nombre: "VTHombro derecho", x: 261, y: 70, ancho: 19, alto: 39 },
  { nombre: "VTBrazo izquierdo", x: 173, y: 108, ancho: 22, alto: 40 },
  { nombre: "VTBrazo derecho", x: 261, y: 108, ancho: 21, alto: 40 },
  { nombre: "VTAntebrazo izquierdo", x: 170, y: 148, ancho: 24, alto: 60 },
  { nombre: "VTAntebrazo derecho", x: 261, y: 148, ancho: 24, alto: 60 },
  { nombre: "VTMano izquierda", x: 169, y: 207, ancho: 20, alto: 39 },
  { nombre: "VTMano derecha", x: 266, y: 207, ancho: 20, alto: 39 },
  { nombre: "VTEspalda Baja", x: 197, y: 140, ancho: 63, alto: 32 },
  { nombre: "VTGluteo Izquierdo", x: 196, y: 176, ancho: 30, alto: 27 },
  { nombre: "VTGluteo Derecho", x: 226, y: 176, ancho: 33, alto: 27 },
  { nombre: "VTMuslo Izquierdo", x: 193, y: 202, ancho: 29, alto: 105 },
  { nombre: "VTMuslo Derecho", x: 233, y: 202, ancho: 29, alto: 105 },
  { nombre: "VTPierna Izquierda", x: 196, y: 307, ancho: 26, alto: 93 },
  { nombre: "VTPierna Derecha", x: 233, y: 307, ancho: 26, alto: 93 },
  { nombre: "VTPie Izquierdo", x: 198, y: 398, ancho: 24, alto: 50 },
  { nombre: "VTPie Derecho", x: 233, y: 398, ancho: 26, alto: 50 },
]

const elementosPorNombre = {}

/**
 * Crea los elementos interactivos para cada parte del cuerpo
 */
function CrearPartesDelCuerpo() {
  const cuerpo = document.getElementById("cuerpoHumano")
  if (!cuerpo) return

  partesDelCuerpo.forEach((parte) => {
    const parteElemento = document.createElement("div")
    parteElemento.classList.add("parteCuerpo")
    parteElemento.style.left = `${parte.x}px`
    parteElemento.style.top = `${parte.y}px`
    parteElemento.style.width = `${parte.ancho}px`
    parteElemento.style.height = `${parte.alto}px`
    parteElemento.setAttribute("title", parte.nombre)
    parteElemento.setAttribute("data-nombre", parte.nombre)

    parteElemento.addEventListener("click", () => {
      mostrarSelectorIntensidad(parte.nombre, parteElemento)
    })

    elementosPorNombre[parte.nombre] = parteElemento
    cuerpo.appendChild(parteElemento)
  })
}

/**
 * Actualiza el color de una parte del cuerpo según la intensidad del dolor
 */
function actualizarColorParte(elemento, intensidad) {
  elemento.classList.remove("dolor-baja", "dolor-media", "dolor-alta")

  if (intensidad) {
    elemento.classList.add(`dolor-${intensidad.toLowerCase()}`)
  }
}

/**
 * Muestra el selector de intensidad de dolor para una parte del cuerpo
 */
function mostrarSelectorIntensidad(nombreParte, elemento) {
  const minitablita = document.getElementById("minitablita")
  if (!minitablita) return

  const filaExistente = Array.from(document.querySelectorAll("#minitablita tr")).find(
    (tr) => tr.cells[0].textContent === nombreParte,
  )

  if (filaExistente) {
    alert("Esta parte del cuerpo ya ha sido seleccionada")
    return
  }

  const intensidades = ["Baja", "Media", "Alta"]
  const tr = document.createElement("tr")
  tr.innerHTML = `
        <td>${nombreParte}</td>
        <input type="hidden" name="ubicacionDolor" value="${nombreParte}">
        <td>
            <select class="form-select" name="intensidad">
                <option value="">Seleccionar intensidad</option>
                ${intensidades
                  .map((intensidad) => `<option value="${intensidad.toLowerCase()}">${intensidad}</option>`)
                  .join("")}
            </select>
        </td>
        <td>
            <button class="btn btn-danger btn-sm eliminar-fila">Eliminar</button>
        </td>
    `

  const select = tr.querySelector("select")
  select.addEventListener("change", (e) => {
    actualizarColorParte(elemento, e.target.value)
  })

  const btnEliminar = tr.querySelector("button")
  btnEliminar.addEventListener("click", () => {
    tr.remove()
    actualizarColorParte(elemento, null)
  })

  minitablita.appendChild(tr)
}

// ============================================================================
// SECCIÓN 7: GESTIÓN DE CHECKBOXES Y SELECCIONES MÚLTIPLES
// ============================================================================

/**
 * Inicializa la gestión de checkboxes mutuamente excluyentes
 */
function inicializarCheckboxesExcluyentes() {
  const checkboxes = document.querySelectorAll(".form-check-input")

  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      const fila = event.target.closest("tr")
      if (fila) {
        fila.querySelectorAll(".form-check-input").forEach((cb) => {
          if (cb !== event.target) {
            cb.checked = false
          }
        })
        return
      }

      const grupo = event.target.closest(".checkbox-group")
      if (grupo) {
        grupo.querySelectorAll(".form-check-input").forEach((cb) => {
          if (cb !== event.target) {
            cb.checked = false
          }
        })
      }
    })
  })
}

/**
 * Inicializa la limitación de selecciones para grupos de checkboxes
 */
function inicializarLimitacionSelecciones() {
  const grupos = [
    { clase: "opcion-checkbox", max: 3 },
    { clase: "opcion-checkbox2", max: 3 },
    { clase: "opcion-checkbox3", max: 1 },
  ]

  grupos.forEach(({ clase, max }) => {
    const checkboxes = document.querySelectorAll(`.${clase}`)

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        const seleccionados = Array.from(checkboxes).filter((chk) => chk.checked)

        if (seleccionados.length > max) {
          checkbox.checked = false
          alert(`Solo puedes seleccionar un máximo de ${max} opciones.`)
        }
      })
    })
  })
}

/**
 * Inicializa los parámetros dinámicos para actividades afectadas
 */
function inicializarParametrosActividades() {
  console.log('🎯 Inicializando parámetros de actividades...');
  const checkboxes = document.querySelectorAll('input[type="checkbox"][name="actividades_afectadas"]')
  console.log('Checkboxes de actividades encontrados:', checkboxes.length);
  const maxSelecciones = 3
  const seleccionadas = new Set()

  checkboxes.forEach((checkbox, index) => {
    if (!checkbox.id) {
      checkbox.id = `actividad_afectada_${index}`
    }

    const paramName = `parametros_${checkbox.id}`

    const parametersSection = document.createElement("div")
    parametersSection.classList.add("parameters-section")
    parametersSection.style.display = "none"

    parametersSection.innerHTML = `
            <div class="form-check">
                <label class="label">
                    <input type="radio" name="${paramName}" class="form-check-input" value="evitativo" />
                    No realizo mucho esta actividad porque miedo a que el dolor empeore
                </label>
            </div>
            <div class="form-check">
                <label class="label">
                    <input type="radio" name="${paramName}" class="form-check-input" value="evitativo" />
                    No realizo esta actividad que me gusta porque el dolor no me deja
                </label>
            </div>
            <div class="form-check">
                <label class="label">
                    <input type="radio" name="${paramName}" class="form-check-input" value="persistente" />
                    Realizo esta actividad pero me detengo o descanso seguido
                </label>
            </div>
            <div class="form-check">
                <label class="label">
                    <input type="radio" name="${paramName}" class="form-check-input" value="persistente" />
                    Realizo esta actividad aunque sienta dolor
                </label>
            </div>
            <div class="form-check">
                <label class="label">
                    <input type="radio" name="${paramName}" class="form-check-input" value="persistente" />
                    Me esfuerzo mucho por hacer esta actividad aunque el dolor persista o moleste
                </label>
            </div>
        `

    const wrapperLabel = checkbox.closest("label")
    const forLabel = document.querySelector(`label[for="${checkbox.id}"]`)
    const anchor = wrapperLabel || forLabel || checkbox

    anchor.insertAdjacentElement("afterend", parametersSection)

    checkbox.addEventListener("change", function () {
      if (this.checked) {
        if (seleccionadas.size >= maxSelecciones) {
          this.checked = false
          alert("Solo puede seleccionar hasta 3 actividades")
          return
        }
        seleccionadas.add(this)
        parametersSection.style.display = "block"
      } else {
        seleccionadas.delete(this)
        parametersSection.style.display = "none"
        parametersSection.querySelectorAll('input[type="radio"]').forEach((cb) => {
          cb.checked = false
        })
      }
    })

    const checkboxesInSection = parametersSection.querySelectorAll('input[type="radio"]')
    checkboxesInSection.forEach((cb) => {
      cb.addEventListener("change", function () {
        if (this.checked) {
          checkboxesInSection.forEach((otherCb) => {
            if (otherCb !== this) {
              otherCb.checked = false
            }
          })
        }
      })
    })
  })
}

// ============================================================================
// SECCIÓN 8: GESTIÓN DE CAMPOS CONDICIONALES
// ============================================================================

/**
 * Inicializa los campos condicionales que se muestran/ocultan según selecciones
 */
function inicializarCamposCondicionales() {
  // Nicotina
  const nicotinaSi = document.getElementById("nicotina")
  const nicotinaNo = document.getElementById("nicotinaNO")
  const opcionesNicotina = document.getElementById("opcionesNicotina")

  if (nicotinaSi && nicotinaNo && opcionesNicotina) {
    nicotinaSi.addEventListener("change", () => {
      if (nicotinaSi.checked) {
        opcionesNicotina.style.display = "block"
      }
    })

    nicotinaNo.addEventListener("change", () => {
      if (nicotinaNo.checked) {
        opcionesNicotina.style.display = "none"
      }
    })
  }

  // Alcohol
  const alcoholSi = document.getElementById("alcoholsi")
  const alcoholNo = document.getElementById("alcoholno")
  const opcionesAlcohol = document.getElementById("opcionesAlcohol")

  if (alcoholSi && alcoholNo && opcionesAlcohol) {
    alcoholSi.addEventListener("change", () => {
      if (alcoholSi.checked) {
        opcionesAlcohol.style.display = "block"
      }
    })

    alcoholNo.addEventListener("change", () => {
      if (alcoholNo.checked) {
        opcionesAlcohol.style.display = "none"
      }
    })
  }

  // Drogas
  const drogasSi = document.getElementById("drogasi")
  const drogasNo = document.getElementById("drogasNO")
  const opcionesDrogas = document.getElementById("opcionesDrogas")

  if (drogasSi && drogasNo && opcionesDrogas) {
    drogasSi.addEventListener("change", () => {
      if (drogasSi.checked) {
        opcionesDrogas.style.display = "block"
      }
    })

    drogasNo.addEventListener("change", () => {
      if (drogasNo.checked) {
        opcionesDrogas.style.display = "none"
      }
    })
  }

  // Marihuana
  const marihuanaSi = document.getElementById("marihuanaSi")
  const marihuanaNo = document.getElementById("marihuanaNo")
  const opcionesMarihuana = document.getElementById("opcionesmarihuana")

  if (marihuanaSi && marihuanaNo && opcionesMarihuana) {
    marihuanaSi.addEventListener("change", () => {
      if (marihuanaSi.checked) {
        opcionesMarihuana.style.display = "block"
      }
    })

    marihuanaNo.addEventListener("change", () => {
      if (marihuanaNo.checked) {
        opcionesMarihuana.style.display = "none"
      }
    })
  }

  // Accidente laboral
  const opdolor1 = document.getElementById("opdolor1")
  const opdolor2 = document.getElementById("opdolor2")

  if (opdolor1) {
    opdolor1.addEventListener("change", toggleCalidadAtencion)
  }
  if (opdolor2) {
    opdolor2.addEventListener("change", toggleCalidadAtencion)
  }
}

// ============================================================================
// SECCIÓN 9: CONTADOR DE TIEMPO
// ============================================================================

/**
 * Inicializa el contador de tiempo para la sesión
 */
function inicializarContadorTiempo() {
  let segundos = 0
  const duracionInput = document.getElementById("duracionSesionInput")

  if (!duracionInput) return

  const actualizarTiempo = () => {
    const horas = Math.floor(segundos / 3600)
    const minutos = Math.floor((segundos % 3600) / 60)
    const seg = segundos % 60

    const formatoTiempo = `${String(horas).padStart(2, "0")}:${String(minutos).padStart(2, "0")}:${String(seg).padStart(2, "0")}`

    duracionInput.value = formatoTiempo
    segundos++
  }

  setInterval(actualizarTiempo, 1000)
}

// ============================================================================
// SECCIÓN 10: UTILIDADES DE INTERFAZ DE USUARIO
// ============================================================================

/**
 * Configurar funcionalidad de mostrar/ocultar contraseña
 * @param {string} passwordInputId - ID del input de contraseña
 * @param {string} toggleButtonId - ID del botón para alternar visibilidad
 */
function setupPasswordToggle(passwordInputId, toggleButtonId) {
  const passwordInput = document.getElementById(passwordInputId)
  const toggleButton = document.getElementById(toggleButtonId)

  if (!passwordInput || !toggleButton) return

  const eyeIcon = toggleButton.querySelector("svg")

  toggleButton.addEventListener("click", function () {
    if (passwordInput.type === "password") {
      passwordInput.type = "text"
      if (eyeIcon) {
        eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.477 0-8.268-2.943-9.542-7a9.956 9.956 0 012.223-3.592m3.62-2.956A9.953 9.953 0 0112 5c4.477 0 8.268 2.943 9.542 7a9.96 9.96 0 01-4.293 5.368M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18" />`
      }
    } else {
      passwordInput.type = "password"
      if (eyeIcon) {
        eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />`
      }
    }
  })
}

// ============================================================================
// SECCIÓN 11: INICIALIZACIÓN DEL FORMULARIO
// ============================================================================

/**
 * Función principal que inicializa todos los componentes del formulario
 */
function inicializarFormulario() {
  // Inicializar validación de RUT
  const rutInput = document.getElementById("rut")
  if (rutInput) {
    rutInput.addEventListener("blur", onBlurRut)
    rutInput.addEventListener("input", manejarRut)
  }


  // Inicializar cálculo de fecha fin
  const fechaInicio = document.getElementById("fecha_inicio")
  const diasLicencia = document.getElementById("dias_licencia")

  if (fechaInicio) {
    fechaInicio.addEventListener("input", calcularFechaFin)
  }
  if (diasLicencia) {
    diasLicencia.addEventListener("input", calcularFechaFin)
  }



  // Limitar fecha de nacimiento para que no se pueda seleccionar el futuro
  const fechaNacInput = document.getElementById('fechaNac');
  if (fechaNacInput) {
    const today = new Date().toISOString().split('T')[0];
    fechaNacInput.setAttribute('max', today);
  }

  // Deshabilitar navegación hasta completar datos personales
  const navButtons = document.querySelectorAll('.nav-section-btn');
  navButtons.forEach(btn => {
    if (btn.getAttribute('data-section') !== 'seccion-datos-paciente') {
      btn.disabled = true;
      btn.classList.add('disabled');
    }
  });

  // Habilitar navegación cuando los datos personales estén completos
  const pacienteSection = document.getElementById('seccion-datos-paciente');
  const requiredInputs = pacienteSection.querySelectorAll('input[required]');
  function checkDatosPersonalesCompletos() {
    let valid = true;
    requiredInputs.forEach(input => {
      if (!input.value.trim()) {
        valid = false;
      }
    });
    navButtons.forEach(btn => {
      if (btn.getAttribute('data-section') !== 'seccion-datos-paciente') {
        btn.disabled = !valid;
        btn.classList.toggle('disabled', !valid);
      }
    });
  }
  requiredInputs.forEach(input => {
    input.addEventListener('input', checkDatosPersonalesCompletos);
    input.addEventListener('blur', checkDatosPersonalesCompletos);
  });
  checkDatosPersonalesCompletos();

  // Inicializar componentes del formulario
  inicializarContadorTiempo();
  inicializarNavegacionSecciones();
  CrearPartesDelCuerpo();
  inicializarCheckboxesExcluyentes();
  inicializarLimitacionSelecciones();
  inicializarParametrosActividades();
  inicializarCamposCondicionales();
}

/**
 * Función principal de inicialización de utilidades
 */
function initializeUtils() {
  inicializarFormatoRUT()
  inicializarValidacionRutLegacy()
}

// ============================================================================
// SECCIÓN 12: CONFIGURACIÓN DE AUTO-INICIALIZACIÓN
// ============================================================================

// Inicializar formulario cuando el DOM esté completamente cargado
document.addEventListener("DOMContentLoaded", function() {
  inicializarFormulario();
  // Listener para el submit del formulario principal
  var form = document.getElementById('Step');
  if (form) {
    form.addEventListener('submit', function(e) {
      // Validación HTML5 automática
      if (!form.checkValidity()) {
        e.preventDefault();
        form.classList.add('was-validated');
        alert('Por favor, completa todos los campos obligatorios correctamente.');
      } else {
        // Debug: Mostrar actividades seleccionadas
        const actividadesSeleccionadas = form.querySelectorAll('input[name="actividades_afectadas"]:checked');
        console.log('📋 Actividades afectadas seleccionadas:', actividadesSeleccionadas.length);
        actividadesSeleccionadas.forEach((act, i) => {
          console.log(`  ${i + 1}. ${act.value}`);
        });
        
        // Recopilar todos los parámetros evitativo/persistente antes de enviar
        recopilarParametrosActividades();
        // Permite el envío normal
        form.classList.remove('was-validated');
      }
    });
  }
  
  /**
   * Recopila todos los valores de parámetros dinámicos y los agrega como campos ocultos
   */
  function recopilarParametrosActividades() {
    const form = document.getElementById('Step');
    
    console.log('🔍 Recopilando parámetros evitativo/persistente...');
    
    // Debug: Ver todos los radios con nombre parametros_
    const todosLosRadios = form.querySelectorAll('input[type="radio"][name^="parametros_"]');
    console.log('Total de radios con parametros_*:', todosLosRadios.length);
    
    // Agrupar por nombre para ver cuántos grupos hay
    const grupos = new Set();
    todosLosRadios.forEach(radio => grupos.add(radio.name));
    console.log('Grupos de parámetros encontrados:', grupos.size);
    grupos.forEach(nombre => console.log('  - ' + nombre));
    
    // Eliminar campos ocultos previos de parámetros (por si se reenvía)
    const camposOcultosAnteriores = form.querySelectorAll('input[name="parametros"]');
    camposOcultosAnteriores.forEach(campo => campo.remove());
    
    // Buscar todos los inputs de radio que empiecen con "parametros_" y estén seleccionados
    const radiosParametros = form.querySelectorAll('input[type="radio"][name^="parametros_"]:checked');
    
    console.log('Total de parámetros seleccionados:', radiosParametros.length);
    
    if (radiosParametros.length === 0) {
      console.warn('⚠️ No se encontraron parámetros seleccionados. Asegúrate de seleccionar actividades y sus opciones.');
      return;
    }
    
    // Crear un campo oculto por cada valor seleccionado
    radiosParametros.forEach((radio, index) => {
      const inputOculto = document.createElement('input');
      inputOculto.type = 'hidden';
      inputOculto.name = 'parametros';
      inputOculto.value = radio.value; // "evitativo" o "persistente"
      form.appendChild(inputOculto);
      
      console.log(`  ✓ Parámetro ${index + 1}: ${radio.name} = ${radio.value}`);
    });
    
    console.log('✅ Parámetros agregados al formulario correctamente');
  }
});

// Compatibilidad con jQuery (si está disponible)
if (typeof jQuery !== "undefined") {
  $(document).ready(function () {
    initializeUtils()
  })
} else {
  // Vanilla JavaScript
  document.addEventListener("DOMContentLoaded", function () {
    initializeUtils()
  })
}

// Inicializar utilidades globales al cargar la página
window.addEventListener("load", () => {
  if (typeof initializeKenkomedUtils === "function") {
    initializeKenkomedUtils()
  }

  if (typeof configurarRUT === "function") {
    configurarRUT({
      formatoTiempoReal: true,
      validacionTiempoReal: true,
      mostrarErrores: true,
    })
  }

  setTimeout(() => {
    if (typeof inicializarFormatoRUT === "function") {
      inicializarFormatoRUT()
    }
  }, 100)
})

// ============================================================================
// SECCIÓN 13: EXPOSICIÓN GLOBAL DE FUNCIONES
// ============================================================================

// Funciones principales del sistema
window.initializeKenkomedUtils = initializeUtils
window.configurarRUT = configurarRUT
window.RUT_CONFIG = RUT_CONFIG

// Funciones de validación y formateo
window.validarRUT = validarRUT
window.formatearRutString = formatearRutString
window.limpiarRUT = limpiarRUT
window.formatoRUT = formatoRUT
window.formatoRUTOnBlur = formatoRUTOnBlur
window.limpiarFormatoRUT = limpiarFormatoRUT

// Funciones legacy para compatibilidad
window.manejarRutLegacy = manejarRutLegacy
window.onBlurRutLegacy = onBlurRutLegacy
window.inicializarValidacionRutLegacy = inicializarValidacionRutLegacy

// Funciones del formulario
window.manejarRut = manejarRut
window.onBlurRut = onBlurRut
window.calcularFechaFin = calcularFechaFin
window.toggleCalidadAtencion = toggleCalidadAtencion
window.inicializarNavegacionSecciones = inicializarNavegacionSecciones
window.marcarSeccionCompletada = marcarSeccionCompletada
window.CrearPartesDelCuerpo = CrearPartesDelCuerpo
window.actualizarColorParte = actualizarColorParte
window.mostrarSelectorIntensidad = mostrarSelectorIntensidad
window.inicializarCheckboxesExcluyentes = inicializarCheckboxesExcluyentes
window.inicializarLimitacionSelecciones = inicializarLimitacionSelecciones
window.inicializarParametrosActividades = inicializarParametrosActividades
window.inicializarCamposCondicionales = inicializarCamposCondicionales
window.inicializarContadorTiempo = inicializarContadorTiempo
window.inicializarFormulario = inicializarFormulario

// Utilidades de UI
window.setupPasswordToggle = setupPasswordToggle

// Variables globales
window.partesDelCuerpo = partesDelCuerpo
window.elementosPorNombre = elementosPorNombre