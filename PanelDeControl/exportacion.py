"""Exportación de ficha clínica completa (portabilidad ARCO)."""
import json
from datetime import date, datetime, time
from decimal import Decimal

from django.forms.models import model_to_dict

from Login.models import (
    Paciente,
    formularioClinico,
    CuestionarioPSFS,
    Groc,
    CuestionarioEQ_5D,
    CuestionarioBarthel,
    CuestionarioScrenning,
    CuestionarioEvaluacionENA,
    RecetaMedica,
    Notas,
    Reserva,
)
from SesionesKinesicas.models import SesionKinesica
from TiposDeFormularios.models import EvaluacionLEFS, EvaluacionOswestry, EvaluacionQuickDASH, EvaluacionWOMAC


def _serializar_valor(valor):
    if valor is None:
        return None
    if isinstance(valor, (datetime, date, time)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (list, dict, str, int, float, bool)):
        return valor
    return str(valor)


def _modelo_a_dict(instancia, excluir=None):
    if instancia is None:
        return None
    data = model_to_dict(instancia, exclude=excluir or [])
    return {k: _serializar_valor(v) for k, v in data.items()}


def _queryset_a_lista(queryset, excluir=None):
    return [_modelo_a_dict(obj, excluir) for obj in queryset]


def exportar_paciente_json(paciente):
    """Arma un dict con todos los datos del paciente en el sistema."""
    data = {
        'exportado_en': datetime.now().isoformat(),
        'formato': 'kenkomed-arco-v1',
        'paciente': _modelo_a_dict(paciente),
        'clinica': _modelo_a_dict(paciente.clinica) if paciente.clinica_id else None,
        'anamnesis': None,
        'notas': None,
        'receta': None,
        'sesiones_kinesicas': [],
        'cuestionarios': {},
        'reservas': [],
    }

    if paciente.clinica_id:
        data['paciente'].pop('clinica', None)

    try:
        data['anamnesis'] = _modelo_a_dict(formularioClinico.objects.get(paciente=paciente))
    except formularioClinico.DoesNotExist:
        pass

    try:
        data['notas'] = _modelo_a_dict(Notas.objects.get(paciente=paciente))
    except Notas.DoesNotExist:
        pass

    try:
        data['receta'] = _modelo_a_dict(RecetaMedica.objects.get(paciente=paciente))
    except RecetaMedica.DoesNotExist:
        pass

    data['sesiones_kinesicas'] = _queryset_a_lista(
        SesionKinesica.objects.filter(paciente=paciente).order_by('numero_sesion')
    )
    data['reservas'] = _queryset_a_lista(
        Reserva.objects.filter(paciente=paciente).order_by('fecha', 'hora_inicio')
    )

    cuestionarios = {}
    for modelo, clave in (
        (CuestionarioPSFS, 'psfs'),
        (Groc, 'groc'),
        (CuestionarioEQ_5D, 'eq5d'),
        (CuestionarioBarthel, 'barthel'),
        (CuestionarioScrenning, 'screening'),
        (CuestionarioEvaluacionENA, 'ena'),
    ):
        try:
            cuestionarios[clave] = _modelo_a_dict(modelo.objects.get(paciente=paciente))
        except modelo.DoesNotExist:
            pass

    cuestionarios['lefs'] = _queryset_a_lista(
        EvaluacionLEFS.objects.filter(paciente=paciente).order_by('-fecha_evaluacion')
    )
    cuestionarios['oswestry'] = _queryset_a_lista(
        EvaluacionOswestry.objects.filter(paciente=paciente).order_by('-fecha_evaluacion')
    )
    cuestionarios['quickdash'] = _queryset_a_lista(
        EvaluacionQuickDASH.objects.filter(paciente=paciente).order_by('-fecha_evaluacion')
    )
    cuestionarios['womac'] = _queryset_a_lista(
        EvaluacionWOMAC.objects.filter(paciente=paciente).order_by('-fecha_evaluacion')
    )
    data['cuestionarios'] = cuestionarios

    return data


def exportar_paciente_json_bytes(paciente):
    payload = exportar_paciente_json(paciente)
    return json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
