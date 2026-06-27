"""Contexto compartido para formularios de identificación de paciente."""
from Login.identificacion_utils import PAISES_DOCUMENTO, TIPOS_DOCUMENTO


def contexto_identificacion_paciente(paciente=None):
    ctx = {
        'tipos_documento': TIPOS_DOCUMENTO,
        'paises_documento': PAISES_DOCUMENTO,
        'tipo_documento_actual': 'rut_chile',
        'pais_documento_actual': '',
        'numero_documento_actual': '',
    }
    if paciente:
        ctx['tipo_documento_actual'] = getattr(paciente, 'tipo_documento', 'rut_chile') or 'rut_chile'
        ctx['pais_documento_actual'] = getattr(paciente, 'pais_documento', '') or ''
        if ctx['tipo_documento_actual'] == 'rut_chile':
            from Login.identificacion_utils import formatear_rut_chileno_display
            ctx['numero_documento_actual'] = formatear_rut_chileno_display(paciente.rut)
        else:
            from Login.identificacion_utils import detectar_tipo_desde_valor_almacenado
            _, pais, numero = detectar_tipo_desde_valor_almacenado(paciente.rut)
            ctx['pais_documento_actual'] = paciente.pais_documento or pais
            ctx['numero_documento_actual'] = numero
    return ctx
