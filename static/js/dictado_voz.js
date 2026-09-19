/**
 * KenkoMed — Motor de Dictado por Voz
 * Usa la Web Speech API nativa del navegador (cero carga en servidor).
 * El audio nunca sale del dispositivo mientras no se acepten términos de terceros.
 */
const DictadoVoz = (() => {
  'use strict';

  let recognition   = null;
  let activeTarget  = null;
  let isListening   = false;
  let finalTranscript = '';

  const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
  const supported = Boolean(SpeechAPI);

  let onStart  = () => {};
  let onStop   = () => {};
  let onError  = () => {};

  function crearRecognition() {
    const rec = new SpeechAPI();
    rec.lang            = 'es-CL';
    rec.interimResults  = true;
    rec.continuous      = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      isListening = true;
      onStart(activeTarget);
    };

    rec.onresult = (e) => {
      const ta = document.getElementById(activeTarget);
      if (!ta) return;
      let interimText = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const resultado = e.results[i];
        if (resultado.isFinal) {
          finalTranscript += resultado[0].transcript + ' ';
        } else {
          interimText += resultado[0].transcript;
        }
      }
      ta.value = finalTranscript + interimText;
      ta.scrollTop = ta.scrollHeight;
    };

    let networkRetries = 0;
    const MAX_RETRIES = 3;

    rec.onerror = (e) => {
      // Error de red: reintentar automáticamente hasta MAX_RETRIES veces
      // (frecuente en modo continuo — Chrome corta la conexión a Google Speech)
      if (e.error === 'network' && isListening && networkRetries < MAX_RETRIES) {
        networkRetries++;
        onError(
          `🔄 Reconectando micrófono (intento ${networkRetries}/${MAX_RETRIES})…`,
          activeTarget
        );
        setTimeout(() => {
          if (isListening && activeTarget) {
            try {
              recognition = crearRecognition();
              recognition.start();
            } catch (_) { _limpiar(); }
          }
        }, 1000);
        return;  // No limpiar — reintentar
      }

      const msgs = {
        'not-allowed':   'Permiso de micrófono denegado. Habilita el acceso en tu navegador.',
        'no-speech':     'No se detectó voz. Intente de nuevo.',
        'audio-capture': 'No se encontró micrófono.',
        'network':       'Sin conexión con el servicio de voz. Verifica tu internet e intenta de nuevo.',
        'aborted':       null,
      };
      const msg = msgs[e.error];
      if (msg) onError(msg, activeTarget);
      _limpiar();
    };


    rec.onend = () => {
      if (isListening && recognition) {
        try { recognition.start(); } catch (_) {}
      } else {
        _limpiar();
      }
    };

    return rec;
  }

  function _limpiar() {
    isListening = false;
    onStop(activeTarget);
    activeTarget    = null;
    finalTranscript = '';
    recognition     = null;
  }

  function iniciar(textareaId) {
    if (!supported) {
      onError('Tu navegador no soporta dictado por voz. Usa Google Chrome o Microsoft Edge.', textareaId);
      return;
    }
    if (isListening && activeTarget === textareaId) {
      detener();
      return;
    }
    if (isListening) detener();
    activeTarget    = textareaId;
    finalTranscript = '';
    const ta = document.getElementById(textareaId);
    if (ta && ta.value.trim()) {
      finalTranscript = ta.value.trimEnd() + ' ';
    }
    recognition = crearRecognition();
    try {
      recognition.start();
    } catch (err) {
      onError('No se pudo iniciar el micrófono: ' + err.message, textareaId);
      _limpiar();
    }
  }

  function detener() {
    if (!isListening || !recognition) return;
    isListening = false;
    try { recognition.stop(); } catch (_) {}
  }

  function configurar(callbacks = {}) {
    if (callbacks.onStart)  onStart  = callbacks.onStart;
    if (callbacks.onStop)   onStop   = callbacks.onStop;
    if (callbacks.onError)  onError  = callbacks.onError;
  }

  return { iniciar, detener, configurar, get isListening() { return isListening; }, supported };
})();
