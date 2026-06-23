"""Vistas de cumplimiento: exportación ARCO y auditoría de accesos."""
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from Login.auditoria import registrar_acceso
from Login.models import AuditoriaAcceso
from ProyectoMainAPP.decorators.login_requerido import requiere_admin_clinica, requiere_clinico
from clinicas.utils import obtener_paciente_por_rut

from .exportacion import exportar_paciente_json_bytes
from .views_informe import RenderFichaClinica


@requiere_clinico
def exportar_ficha(request):
    """
    Exporta la ficha completa del paciente (portabilidad ARCO).
    ?rut=...&format=json|html
    """
    rut = request.GET.get('rut', '').strip()
    formato = request.GET.get('format', 'json').lower()

    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        return HttpResponseForbidden('No tienes permisos para exportar los datos de este paciente.')

    rut_limpio = paciente.rut.replace('.', '').replace('-', '')

    if formato == 'html':
        registrar_acceso(request, paciente, 'exportar_html')
        response = RenderFichaClinica(request)
        if getattr(response, 'status_code', 200) == 200 and hasattr(response, 'content'):
            response['Content-Disposition'] = f'attachment; filename="ficha_{rut_limpio}.html"'
        return response

    registrar_acceso(request, paciente, 'exportar_json')
    contenido = exportar_paciente_json_bytes(paciente)
    response = HttpResponse(contenido, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="ficha_{rut_limpio}.json"'
    return response


@requiere_admin_clinica
def auditoria_accesos(request):
    """Lista accesos a fichas de la clínica (últimos 90 días)."""
    clinica_id = request.session.get('clinica_id')
    es_admin = request.session.get('es_admin', False)

    registros = AuditoriaAcceso.objects.select_related(
        'paciente', 'clinico', 'clinica'
    ).order_by('-fecha')

    if not es_admin and clinica_id:
        registros = registros.filter(clinica_id=clinica_id)

    desde = timezone.now() - timezone.timedelta(days=90)
    registros = registros.filter(fecha__gte=desde)[:500]

    return render(request, 'auditoria_accesos.html', {
        'registros': registros,
        'es_admin': es_admin,
    })
