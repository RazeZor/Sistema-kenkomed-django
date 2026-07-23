from django.shortcuts import get_object_or_404

from ciclos_clinicos.models import CicloClinico


def listar_ciclos_paciente(paciente, clinica_id=None):
    qs = CicloClinico.objects.filter(paciente=paciente).select_related(
        'clinico_responsable', 'clinica',
    )
    if clinica_id:
        qs = qs.filter(clinica_id=clinica_id)
    return qs.order_by('-numero_ciclo')


def obtener_ciclo_activo(paciente, clinica_id):
    if not paciente or not clinica_id:
        return None
    return CicloClinico.objects.filter(
        paciente=paciente,
        clinica_id=clinica_id,
        estado=CicloClinico.ESTADO_ACTIVO,
    ).first()


def obtener_ciclo_por_id(ciclo_id, paciente=None, clinica_id=None):
    if not ciclo_id:
        return None
    qs = CicloClinico.objects.filter(pk=ciclo_id)
    if paciente is not None:
        qs = qs.filter(paciente=paciente)
    if clinica_id:
        qs = qs.filter(clinica_id=clinica_id)
    return qs.first()


def obtener_ciclo_o_404(ciclo_id, paciente=None, clinica_id=None):
    return get_object_or_404(
        CicloClinico.objects.select_related('paciente', 'clinica', 'clinico_responsable'),
        pk=ciclo_id,
        **({'paciente': paciente} if paciente is not None else {}),
        **({'clinica_id': clinica_id} if clinica_id else {}),
    )


def siguiente_numero_ciclo(paciente, clinica_id):
    ultimo = CicloClinico.objects.filter(
        paciente=paciente,
        clinica_id=clinica_id,
    ).order_by('-numero_ciclo').values_list('numero_ciclo', flat=True).first()
    return (ultimo or 0) + 1
