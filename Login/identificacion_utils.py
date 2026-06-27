"""Validación y normalización de identificadores de paciente (RUT chileno y documentos extranjeros)."""
import re

from Login.paises_data import paises_documento_para_select, nombre_pais

TIPO_RUT_CHILE = 'rut_chile'
TIPO_PASAPORTE = 'pasaporte'
TIPO_DNI_EXTRANJERO = 'dni_extranjero'
TIPO_OTRO = 'otro'

TIPOS_DOCUMENTO = (
    (TIPO_RUT_CHILE, 'RUT chileno'),
    (TIPO_PASAPORTE, 'Pasaporte'),
    (TIPO_DNI_EXTRANJERO, 'DNI / Documento extranjero'),
    (TIPO_OTRO, 'Otro documento'),
)

# ISO 3166-1 (263 territorios, nombres en español) — ver Login/data/paises_es.json
PAISES_DOCUMENTO = tuple(paises_documento_para_select())

_PREFIJOS = {
    TIPO_PASAPORTE: 'P',
    TIPO_DNI_EXTRANJERO: 'D',
    TIPO_OTRO: 'O',
}

_DOC_EXTRANJERO_RE = re.compile(r'^[A-Za-z0-9\-]{4,24}$')


def validar_rut_chileno(rut):
    """Valida RUT chileno (módulo 11)."""
    rut = str(rut).replace('.', '').replace('-', '').upper().strip()
    if len(rut) < 2:
        return False
    cuerpo, dv = rut[:-1], rut[-1]
    if not cuerpo.isdigit():
        return False
    suma, multiplo = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    resto = suma % 11
    dv_esperado = str(11 - resto)
    if dv_esperado == '11':
        dv_esperado = '0'
    elif dv_esperado == '10':
        dv_esperado = 'K'
    return dv == dv_esperado


def normalizar_rut_chileno(rut):
    """RUT sin puntos: 12345678-9"""
    limpio = str(rut).replace('.', '').replace('-', '').upper().strip()
    if len(limpio) < 2:
        return limpio
    return f'{limpio[:-1]}-{limpio[-1]}'


def formatear_rut_chileno_display(rut):
    """RUT con puntos para mostrar."""
    norm = normalizar_rut_chileno(rut)
    if len(norm) < 3 or '-' not in norm:
        return rut
    cuerpo, dv = norm.split('-', 1)
    cuerpo_fmt = ''
    while len(cuerpo) > 3:
        cuerpo_fmt = '.' + cuerpo[-3:] + cuerpo_fmt
        cuerpo = cuerpo[:-3]
    return f'{cuerpo}{cuerpo_fmt}-{dv}'


def _limpiar_numero_extranjero(numero):
    return re.sub(r'[^A-Za-z0-9]', '', str(numero or '')).upper()


def _normalizar_pais(pais):
    p = str(pais or '').strip().upper()[:3]
    return p or 'XX'


def detectar_tipo_desde_valor_almacenado(valor):
    """Infiera tipo/pais/número desde el identificador guardado en BD."""
    if not valor:
        return TIPO_RUT_CHILE, '', ''
    val = str(valor).strip()
    if val.startswith(('P-', 'D-', 'O-')):
        partes = val.split('-', 2)
        if len(partes) == 3:
            pref, pais, numero = partes
            tipo_map = {'P': TIPO_PASAPORTE, 'D': TIPO_DNI_EXTRANJERO, 'O': TIPO_OTRO}
            return tipo_map.get(pref, TIPO_OTRO), pais, numero
    return TIPO_RUT_CHILE, 'CL', val


def normalizar_identificador(tipo_documento, numero, pais_documento=''):
    """Genera el identificador canónico para guardar como PK."""
    tipo = tipo_documento or TIPO_RUT_CHILE
    if tipo == TIPO_RUT_CHILE:
        return normalizar_rut_chileno(numero)
    pais = _normalizar_pais(pais_documento)
    num = _limpiar_numero_extranjero(numero)
    pref = _PREFIJOS.get(tipo, 'O')
    return f'{pref}-{pais}-{num}'


def validar_identificacion(tipo_documento, numero, pais_documento=''):
    """Retorna (ok: bool, mensaje_error: str)."""
    tipo = tipo_documento or TIPO_RUT_CHILE
    numero = str(numero or '').strip()
    if not numero:
        return False, 'El número de documento es obligatorio'

    if tipo == TIPO_RUT_CHILE:
        if not validar_rut_chileno(numero):
            return False, 'El RUT ingresado no es válido'
        return True, ''

    pais = _normalizar_pais(pais_documento)
    if not pais or pais == 'XX':
        return False, 'Seleccione el país de emisión del documento'

    limpio = _limpiar_numero_extranjero(numero)
    if not _DOC_EXTRANJERO_RE.match(limpio):
        return False, 'Documento inválido: use 4–24 caracteres alfanuméricos'
    return True, ''


def variantes_busqueda_identificador(valor, tipo_documento=None, pais_documento=None):
    """Variantes posibles del identificador para búsqueda (compatibilidad legacy)."""
    valor = str(valor or '').strip()
    if not valor:
        return []

    if valor.startswith(('P-', 'D-', 'O-')):
        return [valor]

    tipo = tipo_documento or TIPO_RUT_CHILE
    if tipo != TIPO_RUT_CHILE:
        canonico = normalizar_identificador(tipo, valor, pais_documento)
        return list({canonico, valor.upper()})

    variantes = {valor, valor.upper()}
    norm = normalizar_rut_chileno(valor)
    variantes.add(norm)
    variantes.add(formatear_rut_chileno_display(norm))
    variantes.add(valor.replace('.', '').replace('-', '').upper())
    return [v for v in variantes if v]


def resolver_paciente_por_identificacion(valor, tipo_documento=None, pais_documento=None):
    """Busca Paciente por identificador con variantes."""
    from Login.models import Paciente

    for candidato in variantes_busqueda_identificador(valor, tipo_documento, pais_documento):
        try:
            return Paciente.objects.get(rut=candidato)
        except Paciente.DoesNotExist:
            continue
    return None


def identificacion_ya_existe(tipo_documento, numero, pais_documento=''):
    from Login.models import Paciente

    canonico = normalizar_identificador(tipo_documento, numero, pais_documento)
    if Paciente.objects.filter(rut=canonico).exists():
        return True
    for v in variantes_busqueda_identificador(numero, tipo_documento, pais_documento):
        if Paciente.objects.filter(rut=v).exists():
            return True
    return False


def formatear_identificacion_display(paciente):
    """Texto legible para UI."""
    tipo = getattr(paciente, 'tipo_documento', TIPO_RUT_CHILE) or TIPO_RUT_CHILE
    pais = getattr(paciente, 'pais_documento', '') or ''
    rut = paciente.rut

    if tipo == TIPO_RUT_CHILE or not rut.startswith(('P-', 'D-', 'O-')):
        return formatear_rut_chileno_display(rut)

    _, pais_stored, numero = detectar_tipo_desde_valor_almacenado(rut)
    pais_label = nombre_pais(pais or pais_stored) or (pais or pais_stored)
    labels = dict(TIPOS_DOCUMENTO)
    return f'{labels.get(tipo, "Documento")} ({pais_label}): {numero}'


def etiqueta_tipo_documento(tipo):
    return dict(TIPOS_DOCUMENTO).get(tipo, tipo)


def identificacion_coincide_con_paciente(paciente, valor_ingresado):
    """True si el documento ingresado corresponde al paciente."""
    valor = str(valor_ingresado or '').strip()
    if not valor or not paciente:
        return False
    tipo = getattr(paciente, 'tipo_documento', TIPO_RUT_CHILE) or TIPO_RUT_CHILE
    pais = getattr(paciente, 'pais_documento', '') or ''
    if not pais and tipo != TIPO_RUT_CHILE:
        _, pais_detectado, _ = detectar_tipo_desde_valor_almacenado(paciente.rut)
        pais = pais_detectado or pais
    canonico = normalizar_identificador(tipo, valor, pais)
    if canonico == paciente.rut:
        return True
    for candidato in variantes_busqueda_identificador(valor, tipo, pais):
        if candidato == paciente.rut:
            return True
    return False
