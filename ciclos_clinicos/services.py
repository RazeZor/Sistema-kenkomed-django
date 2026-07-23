from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ciclos_clinicos.models import CicloClinico
from ciclos_clinicos.permissions import ciclo_pertenece_a_sesion
from ciclos_clinicos.selectors import (
    obtener_ciclo_activo,
    obtener_ciclo_por_id,
    siguiente_numero_ciclo,
)


class CicloClinicoError(ValidationError):
    """Error de reglas de negocio para ciclos clínicos."""


def _registrar_auditoria_ciclo(request, accion, ciclo, detalle=''):
    try:
        from Login.auditoria import registrar_auditoria
        registrar_auditoria(request, accion, ciclo.paciente, detalle=detalle)
    except Exception:
        pass


@transaction.atomic
def iniciar_nuevo_ciclo(paciente, clinica, clinico, motivo_consulta='', request=None):
    if not paciente or not clinica:
        raise CicloClinicoError('Paciente y clínica son obligatorios para iniciar un ciclo.')

    activo = obtener_ciclo_activo(paciente, clinica.id)
    if activo:
        raise CicloClinicoError(
            'Ya existe un ciclo clínico activo. Finalícelo o abandónelo antes de iniciar uno nuevo.'
        )

    ciclo = CicloClinico.objects.create(
        paciente=paciente,
        clinica=clinica,
        clinico_responsable=clinico,
        numero_ciclo=siguiente_numero_ciclo(paciente, clinica.id),
        estado=CicloClinico.ESTADO_ACTIVO,
        motivo_consulta=motivo_consulta or '',
    )

    if request:
        _registrar_auditoria_ciclo(
            request,
            'inicio_ciclo_clinico',
            ciclo,
            detalle=f'Inició ciclo #{ciclo.numero_ciclo} — {paciente.rut}',
        )
    return ciclo


@transaction.atomic
def finalizar_ciclo(ciclo, clinico=None, notas_cierre='', request=None):
    if not ciclo:
        raise CicloClinicoError('Ciclo no encontrado.')
    if ciclo.estado != CicloClinico.ESTADO_ACTIVO:
        raise CicloClinicoError('Solo se puede finalizar un ciclo activo.')

    ciclo.estado = CicloClinico.ESTADO_FINALIZADO
    ciclo.fecha_cierre = timezone.now()
    if notas_cierre:
        ciclo.notas_cierre = notas_cierre
    if clinico and not ciclo.clinico_responsable_id:
        ciclo.clinico_responsable = clinico
    ciclo.save(update_fields=['estado', 'fecha_cierre', 'notas_cierre', 'clinico_responsable'])

    if request:
        _registrar_auditoria_ciclo(
            request,
            'cierre_ciclo_clinico',
            ciclo,
            detalle=f'Finalizó ciclo #{ciclo.numero_ciclo} — {ciclo.paciente.rut}',
        )
    return ciclo


@transaction.atomic
def abandonar_ciclo(ciclo, clinico=None, motivo='', request=None):
    if not ciclo:
        raise CicloClinicoError('Ciclo no encontrado.')
    if ciclo.estado != CicloClinico.ESTADO_ACTIVO:
        raise CicloClinicoError('Solo se puede abandonar un ciclo activo.')

    ciclo.estado = CicloClinico.ESTADO_ABANDONADO
    ciclo.fecha_cierre = timezone.now()
    if motivo:
        ciclo.notas_cierre = motivo
    if clinico and not ciclo.clinico_responsable_id:
        ciclo.clinico_responsable = clinico
    ciclo.save(update_fields=['estado', 'fecha_cierre', 'notas_cierre', 'clinico_responsable'])

    if request:
        _registrar_auditoria_ciclo(
            request,
            'cierre_ciclo_clinico',
            ciclo,
            detalle=f'Abandonó ciclo #{ciclo.numero_ciclo} — {ciclo.paciente.rut}',
        )
    return ciclo


def obtener_ciclo_desde_request(request, paciente, crear_si_ausente=False, clinico=None):
    """
    Resuelve el ciclo clínico desde ?ciclo_id=, sesión o ciclo activo.
    Si crear_si_ausente=True y no hay ciclo activo, inicia ciclo #1.
    """
    clinica_id = request.session.get('clinica_id') or (paciente.clinica_id if paciente else None)
    ciclo_id = request.GET.get('ciclo_id') or request.POST.get('ciclo_id')

    if ciclo_id:
        ciclo = obtener_ciclo_por_id(ciclo_id, paciente=paciente, clinica_id=clinica_id)
        if ciclo and ciclo_pertenece_a_sesion(request, ciclo):
            request.session['ciclo_activo_id'] = ciclo.id
            return ciclo
        return None

    session_ciclo_id = request.session.get('ciclo_activo_id')
    if session_ciclo_id:
        ciclo = obtener_ciclo_por_id(session_ciclo_id, paciente=paciente, clinica_id=clinica_id)
        if ciclo and ciclo_pertenece_a_sesion(request, ciclo):
            return ciclo

    ciclo = obtener_ciclo_activo(paciente, clinica_id)
    if ciclo:
        request.session['ciclo_activo_id'] = ciclo.id
        return ciclo

    if crear_si_ausente and paciente and clinica_id and paciente.clinica_id:
        clinica = paciente.clinica
        ciclo = iniciar_nuevo_ciclo(paciente, clinica, clinico, request=request)
        request.session['ciclo_activo_id'] = ciclo.id
        return ciclo

    return None


def asegurar_ciclo_editable(ciclo):
    if ciclo and ciclo.es_solo_lectura:
        raise CicloClinicoError('Este ciclo clínico está cerrado y es de solo lectura.')


def querystring_ciclo(ciclo):
    return f'ciclo_id={ciclo.id}' if ciclo else ''
