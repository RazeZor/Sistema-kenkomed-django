/**
 * Identificación de paciente: campo RUT chileno O campo documento extranjero (mutuamente excluyentes).
 */
(function () {
  const LABELS = {
    pasaporte: 'N° pasaporte',
    dni_extranjero: 'N° documento',
    otro: 'N° identificación',
  };

  const PLACEHOLDERS = {
    pasaporte: 'Ej: AB1234567',
    dni_extranjero: 'Ej: 12345678',
    otro: 'Número o código',
  };

  const AYUDAS = {
    pasaporte: 'Pasaporte: letras y números, 4–24 caracteres',
    dni_extranjero: 'Documento de identidad del país de origen',
    otro: 'Identificador único del paciente',
  };

  function validarRUTChileno(rut) {
    if (typeof window.validarRUT === 'function') {
      return window.validarRUT(rut);
    }
    return true;
  }

  function formatoRUTInput(input) {
    if (typeof window.formatoRUT === 'function') {
      window.formatoRUT(input);
    }
  }

  function validarDocumentoExtranjero(valor) {
    const limpio = String(valor || '').replace(/[^A-Za-z0-9]/g, '');
    return limpio.length >= 4 && limpio.length <= 24;
  }

  function activarCampoRUT(bloque, inputRut, inputExt, fieldName) {
    const wrapRut = bloque.querySelector('.identificacion-wrap-rut');
    const wrapExt = bloque.querySelector('.identificacion-wrap-extranjero');
    if (wrapRut) wrapRut.style.display = '';
    if (wrapExt) wrapExt.style.display = 'none';

    if (inputRut) {
      inputRut.disabled = false;
      inputRut.required = true;
      inputRut.setAttribute('name', fieldName);
    }
    if (inputExt) {
      inputExt.disabled = true;
      inputExt.required = false;
      inputExt.removeAttribute('name');
      inputExt.classList.remove('border-red-500', 'border-green-500', 'is-valid', 'is-invalid');
    }
  }

  function activarCampoExtranjero(bloque, inputRut, inputExt, fieldName, tipo) {
    const wrapRut = bloque.querySelector('.identificacion-wrap-rut');
    const wrapExt = bloque.querySelector('.identificacion-wrap-extranjero');
    if (wrapRut) wrapRut.style.display = 'none';
    if (wrapExt) wrapExt.style.display = '';

    if (inputRut) {
      inputRut.disabled = true;
      inputRut.required = false;
      inputRut.removeAttribute('name');
      inputRut.classList.remove('border-red-500', 'border-green-500', 'is-valid', 'is-invalid');
    }
    if (inputExt) {
      inputExt.disabled = false;
      inputExt.required = true;
      inputExt.setAttribute('name', fieldName);
      inputExt.placeholder = PLACEHOLDERS[tipo] || 'Número o código';
    }

    const labelNum = bloque.querySelector('.identificacion-label-numero');
    if (labelNum) labelNum.textContent = LABELS[tipo] || 'N° documento';
    const ayuda = bloque.querySelector('.identificacion-ayuda');
    if (ayuda) ayuda.textContent = AYUDAS[tipo] || 'Letras y números, 4–24 caracteres';
  }

  function configurarBusquedaPais(bloque, paisSelect) {
    const busqueda = bloque.querySelector('.identificacion-pais-busqueda');
    if (!busqueda || !paisSelect || paisSelect.dataset.paisBusquedaOk) return;
    paisSelect.dataset.paisBusquedaOk = 'true';

    const opciones = Array.from(paisSelect.options).map((opt) => ({
      value: opt.value,
      text: opt.text,
      element: opt,
    }));

    function filtrarPaises() {
      const q = busqueda.value.trim().toLowerCase();
      let visibles = 0;
      opciones.forEach(({ value, text, element }) => {
        const coincide = !q || !value || text.toLowerCase().includes(q) || value.toLowerCase().includes(q);
        element.hidden = !coincide;
        if (coincide) visibles += 1;
      });
      if (q && visibles === 1) {
        const unica = opciones.find((o) => !o.element.hidden && o.value);
        if (unica) paisSelect.value = unica.value;
      }
    }

    busqueda.addEventListener('input', filtrarPaises);
    busqueda.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const primera = opciones.find((o) => !o.element.hidden && o.value);
        if (primera) {
          paisSelect.value = primera.value;
          busqueda.value = primera.text;
        }
      }
    });
    paisSelect.addEventListener('change', () => {
      const sel = paisSelect.selectedOptions[0];
      if (sel && sel.value) busqueda.value = sel.text;
    });
    const sel = paisSelect.selectedOptions[0];
    if (sel && sel.value) busqueda.value = sel.text;
  }

  function configurarBloqueIdentificacion(bloque) {
    const tipoSelect = bloque.querySelector('.identificacion-tipo');
    const paisWrap = bloque.querySelector('.identificacion-pais-wrap');
    const paisSelect = bloque.querySelector('.identificacion-pais');
    const inputRut = bloque.querySelector('.identificacion-input-rut');
    const inputExt = bloque.querySelector('.identificacion-input-extranjero');
    const fieldName = bloque.dataset.inputName || 'numero_documento';

    if (!tipoSelect || !inputRut || !inputExt) return;

    bloque.dataset.identificacionManaged = 'true';

    function actualizarUI() {
      const tipo = tipoSelect.value || 'rut_chile';
      const esRut = tipo === 'rut_chile';

      if (paisWrap) paisWrap.style.display = esRut ? 'none' : '';
      if (paisSelect) paisSelect.required = !esRut;

      if (esRut) {
        activarCampoRUT(bloque, inputRut, inputExt, fieldName);
      } else {
        activarCampoExtranjero(bloque, inputRut, inputExt, fieldName, tipo);
      }
    }

    function validarVisualRut() {
      const val = inputRut.value.trim();
      if (!val || inputRut.disabled) {
        inputRut.classList.remove('border-green-500', 'border-red-500', 'is-valid', 'is-invalid');
        return true;
      }
      const ok = validarRUTChileno(val);
      inputRut.classList.toggle('border-red-500', !ok);
      inputRut.classList.toggle('is-invalid', !ok);
      inputRut.classList.toggle('border-green-500', ok);
      inputRut.classList.toggle('is-valid', ok);
      return ok;
    }

    function validarVisualExt() {
      const val = inputExt.value.trim();
      if (!val || inputExt.disabled) {
        inputExt.classList.remove('border-green-500', 'border-red-500', 'is-valid', 'is-invalid');
        return true;
      }
      const ok = validarDocumentoExtranjero(val) && paisSelect && paisSelect.value;
      inputExt.classList.toggle('border-red-500', !ok);
      inputExt.classList.toggle('is-invalid', !ok);
      inputExt.classList.toggle('border-green-500', ok);
      inputExt.classList.toggle('is-valid', ok);
      return ok;
    }

    tipoSelect.addEventListener('change', () => {
      actualizarUI();
      validarVisualRut();
      validarVisualExt();
    });

    inputRut.addEventListener('input', () => {
      formatoRUTInput(inputRut);
      validarVisualRut();
    });
    inputRut.addEventListener('blur', validarVisualRut);

    inputExt.addEventListener('input', () => {
      inputExt.value = inputExt.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
      validarVisualExt();
    });
    inputExt.addEventListener('blur', validarVisualExt);

    configurarBusquedaPais(bloque, paisSelect);

    actualizarUI();
    if (inputRut.value) validarVisualRut();
    if (inputExt.value) validarVisualExt();
  }

  function inicializarIdentificacionPaciente(root) {
    const scope = root || document;
    scope.querySelectorAll('.campo-identificacion-paciente, .identificacion-busqueda').forEach(configurarBloqueIdentificacion);
  }

  function obtenerInputActivo(bloque) {
    const tipo = bloque.querySelector('.identificacion-tipo')?.value || 'rut_chile';
    if (tipo === 'rut_chile') {
      return bloque.querySelector('.identificacion-input-rut');
    }
    return bloque.querySelector('.identificacion-input-extranjero');
  }

  function validarFormularioIdentificacion(form) {
    const bloque = form.querySelector('.campo-identificacion-paciente, .identificacion-busqueda');
    if (!bloque) return true;

    const tipo = bloque.querySelector('.identificacion-tipo')?.value || 'rut_chile';
    const input = obtenerInputActivo(bloque);
    const pais = bloque.querySelector('.identificacion-pais');

    if (!input || !input.value.trim()) {
      alert('Ingrese el número de documento');
      input?.focus();
      return false;
    }

    if (tipo === 'rut_chile') {
      if (!validarRUTChileno(input.value)) {
        alert('El RUT ingresado no es válido');
        input.focus();
        return false;
      }
    } else {
      if (!pais || !pais.value) {
        alert('Seleccione el país de emisión del documento');
        pais?.focus();
        return false;
      }
      if (!validarDocumentoExtranjero(input.value)) {
        alert('Documento inválido (4–24 caracteres alfanuméricos)');
        input.focus();
        return false;
      }
    }
    return true;
  }

  window.inicializarIdentificacionPaciente = inicializarIdentificacionPaciente;
  window.validarFormularioIdentificacion = validarFormularioIdentificacion;

  document.addEventListener('DOMContentLoaded', function () {
    inicializarIdentificacionPaciente();
  });
})();
