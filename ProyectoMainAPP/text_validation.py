"""Validación de texto plano: rechaza HTML, CSS y JavaScript antes de guardar en BD."""
import html
import re
from typing import Optional

_HTML_TAG_RE = re.compile(r'<\s*/?\s*[a-zA-Z][^>]*>', re.DOTALL)
_HTML_ENTITY_RE = re.compile(
    r'&(?:lt|gt|#x0*3c|#0*60|#x0*3e|#0*62)\b',
    re.IGNORECASE,
)
_EVENT_HANDLER_RE = re.compile(r'\bon[a-z]+\s*=', re.IGNORECASE)
_JS_URL_RE = re.compile(r'javascript\s*:', re.IGNORECASE)
_CSS_INJECTION_RE = re.compile(
    r'(?:<\s*style\b|@\s*(?:import|charset|keyframes)\b|expression\s*\()',
    re.IGNORECASE,
)


class TextoPlanoInvalidoError(ValueError):
    """El valor contiene marcado o código no permitido."""

    def __init__(self, campo: str, motivo: str):
        self.campo = campo
        self.motivo = motivo
        super().__init__(f'{campo}: {motivo}')


def _normalizar_para_revision(valor) -> str:
    if valor is None:
        return ''
    texto = str(valor).strip()
    if not texto:
        return ''
    return html.unescape(texto)


def motivo_texto_no_plano(valor) -> Optional[str]:
    """
    Retorna un mensaje de error si el valor no es texto plano seguro, o None si es válido.
    """
    if valor is None:
        return None
    crudo = str(valor).strip()
    if not crudo:
        return None

    if _HTML_ENTITY_RE.search(crudo):
        return 'No se permiten entidades HTML (&lt;, &gt;). Escriba solo texto plano.'

    texto = _normalizar_para_revision(crudo)

    if _HTML_TAG_RE.search(texto):
        return 'No se permiten etiquetas HTML. Escriba solo texto plano.'

    if _EVENT_HANDLER_RE.search(texto):
        return 'No se permiten atributos de eventos JavaScript (onclick, onerror, etc.).'

    if _JS_URL_RE.search(texto):
        return 'No se permiten enlaces javascript:. Escriba solo texto plano.'

    if _CSS_INJECTION_RE.search(texto):
        return 'No se permiten estilos CSS embebidos. Escriba solo texto plano.'

    return None


def validar_texto_plano(valor, nombre_campo: str) -> None:
    motivo = motivo_texto_no_plano(valor)
    if motivo:
        raise TextoPlanoInvalidoError(nombre_campo, motivo)


def validar_campos_texto_plano(
    campos: dict,
    etiquetas: Optional[dict] = None,
) -> list[str]:
    """Valida un dict campo → valor. Retorna lista de mensajes para mostrar al usuario."""
    etiquetas = etiquetas or {}
    errores: list[str] = []
    for clave, valor in campos.items():
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            continue
        motivo = motivo_texto_no_plano(valor)
        if motivo:
            etiqueta = etiquetas.get(clave, clave.replace('_', ' ').title())
            errores.append(f'{etiqueta}: {motivo}')
    return errores
