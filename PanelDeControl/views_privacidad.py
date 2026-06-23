"""Vistas de cumplimiento: exportación ARCO y auditoría de accesos."""
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from Login.auditoria import registrar_auditoria
from Login.models import AuditoriaAcceso, Clinico
from ProyectoMainAPP.decorators.login_requerido import requiere_admin_auditoria, requiere_clinico
from clinicas.utils import (
    filtrar_auditoria_por_sesion,
    obtener_clinica_de_sesion,
    obtener_paciente_por_rut,
)

from .auditoria_pdf import generar_auditoria_pdf
from .exportacion import exportar_paciente_json_bytes
from .views_informe import RenderFichaClinica

DIAS_PERMITIDOS = (30, 90, 180)


def _dias_desde_request(request):
    try:
        dias = int(request.GET.get('dias', 90))
    except (TypeError, ValueError):
        dias = 90
    if dias not in DIAS_PERMITIDOS:
        dias = 90
    return dias


def _queryset_auditoria(request, dias):
    desde = timezone.now() - timezone.timedelta(days=dias)
    return list(
        filtrar_auditoria_por_sesion(
            request,
            AuditoriaAcceso.objects.select_related('paciente', 'clinico', 'clinica'),
        )
        .filter(fecha__gte=desde)
        .order_by('-fecha')[:1000]
    )


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
        registrar_auditoria(
            request, 'exportacion_arco_html', paciente,
            detalle=f'Exportación ARCO HTML — paciente {paciente.rut}',
        )
        request.auditoria_suprimida = True
        response = RenderFichaClinica(request)
        if getattr(response, 'status_code', 200) == 200 and hasattr(response, 'content'):
            response['Content-Disposition'] = f'attachment; filename="ficha_{rut_limpio}.html"'
        return response

    registrar_auditoria(
        request, 'exportacion_arco_json', paciente,
        detalle=f'Exportación ARCO JSON — paciente {paciente.rut}',
    )
    contenido = exportar_paciente_json_bytes(paciente)
    response = HttpResponse(contenido, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="ficha_{rut_limpio}.json"'
    return response


@requiere_admin_auditoria
def auditoria_accesos(request):
    """Lista acciones clínicas auditadas del centro activo."""
    dias = _dias_desde_request(request)
    registros = _queryset_auditoria(request, dias)
    clinica = obtener_clinica_de_sesion(request)

    return render(request, 'auditoria_accesos.html', {
        'registros': registros,
        'clinica': clinica,
        'dias': dias,
        'dias_opciones': DIAS_PERMITIDOS,
    })


@requiere_admin_auditoria
def exportar_auditoria_pdf(request):
    """Exporta el registro de auditoría del centro en PDF."""
    dias = _dias_desde_request(request)
    registros = _queryset_auditoria(request, dias)
    clinica = obtener_clinica_de_sesion(request)

    rut_sesion = request.session.get('rut_clinico')
    clinico = Clinico.objects.filter(rut=rut_sesion).first() if rut_sesion else None
    generado_por = ''
    if clinico:
        generado_por = f'{clinico.nombre} {clinico.apellido}'
        if request.session.get('es_admin'):
            generado_por += ' (Admin KenkoMed)'
        elif request.session.get('es_admin_clinica'):
            generado_por += ' (Admin centro)'

    registrar_auditoria(
        request, 'exportacion_auditoria_pdf', paciente=None,
        detalle=f'Exportación PDF — últimos {dias} días — {len(registros)} registros',
    )

    pdf_bytes = generar_auditoria_pdf(clinica, registros, dias, generado_por=generado_por)
    nombre_centro = (clinica.nombre if clinica else 'centro').replace(' ', '_')[:30]
    fecha_str = timezone.localtime(timezone.now()).strftime('%Y%m%d')
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="auditoria_{nombre_centro}_{fecha_str}.pdf"'
    )
    return response
