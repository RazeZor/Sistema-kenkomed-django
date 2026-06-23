"""Métricas reales del panel de control (consultas a BD)."""
from datetime import timedelta

from django.utils import timezone

from Login.models import Reserva, formularioClinico
from SesionesKinesicas.models import SesionKinesica
from clinicas.utils import (
    filtrar_pacientes_por_sesion,
    filtrar_por_clinica_sesion,
    filtrar_reservas_por_sesion,
)


def _reservas_para_metricas(request):
    """Admin del centro: todas las citas del equipo. Miembro: solo las propias."""
    if request.session.get('es_admin_clinica'):
        return filtrar_reservas_por_sesion(request)
    rut = request.session.get('rut_clinico')
    if rut:
        return Reserva.objects.filter(clinico_id=rut)
    return Reserva.objects.none()


def obtener_metricas_panel(request):
    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    inicio_mes = hoy.replace(day=1)

    pacientes_qs = filtrar_pacientes_por_sesion(request)
    paciente_ids = list(pacientes_qs.values_list('pk', flat=True))
    reservas_qs = _reservas_para_metricas(request)
    reservas_activas = reservas_qs.exclude(estado='Cancelada')

    formularios_qs = filtrar_por_clinica_sesion(
        request,
        formularioClinico.objects.all(),
        lookup='paciente__clinica_id',
    )

    sesiones_qs = (
        SesionKinesica.objects.filter(paciente_id__in=paciente_ids)
        if paciente_ids
        else SesionKinesica.objects.none()
    )

    es_admin_centro = bool(request.session.get('es_admin_clinica'))

    # Paciente no tiene fecha de alta; usamos anamnesis registradas este mes
    anamnesis_nuevas_mes = formularios_qs.filter(
        fechaCreacion__date__gte=inicio_mes,
    ).values('paciente').distinct().count()

    return {
        'total_pacientes': pacientes_qs.count(),
        'anamnesis_nuevas_mes': anamnesis_nuevas_mes,
        'citas_hoy': reservas_activas.filter(fecha=hoy).count(),
        'citas_semana': reservas_activas.filter(
            fecha__gte=inicio_semana,
            fecha__lte=fin_semana,
        ).count(),
        'formularios_completados': formularios_qs.count(),
        'sesiones_kinesicas': sesiones_qs.count(),
        'metricas_alcance_centro': es_admin_centro,
        'etiqueta_citas_semana': (
            'Citas del centro esta semana' if es_admin_centro else 'Mis citas esta semana'
        ),
        'etiqueta_citas_hoy': (
            'Citas del centro hoy' if es_admin_centro else 'Mis citas hoy'
        ),
    }
