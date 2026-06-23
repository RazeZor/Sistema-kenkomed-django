"""Vincula escalas/cuestionarios clínicos con sesiones kinésicas."""
from django.urls import reverse

from .models import RegistroEscalaSesion, SesionKinesica

ESCALAS_MENU = (
    ('psfs', 'PSFS', 'gestionar_psfs', 'Escala funcional específica del paciente'),
    ('groc', 'GROC', 'GROK', 'Cambio global percibido'),
    ('eq5d', 'EQ-5D', 'EQ_5D', 'Calidad de vida y EVA'),
    ('barthel', 'Barthel', 'bartel', 'Índice de Barthel'),
    ('ena', 'ENA', 'ENA', 'Escala numérica análoga'),
    ('screening', 'Screening', 'Screnning', 'Screening Örebro'),
    ('oswestry', 'Oswestry ODI', 'oswestry', 'Incapacidad lumbar'),
    ('lefs', 'LEFS', 'lefs', 'Funcionalidad extremidad inferior'),
)


def numero_sesion_desde_request(request, rut_paciente=None):
    """Lee el número de sesión kinésica desde POST, GET o sesión Django."""
    raw = (
        request.POST.get('numero_sesion_kine')
        or request.POST.get('numero_sesion')
        or request.GET.get('numero_sesion_kine')
        or request.GET.get('numero_sesion')
        or ''
    )
    if raw:
        try:
            numero = int(raw)
            if rut_paciente:
                request.session[f'escala_sesion_kine_{rut_paciente}'] = numero
            return numero
        except (TypeError, ValueError):
            pass
    if rut_paciente:
        guardado = request.session.get(f'escala_sesion_kine_{rut_paciente}')
        if guardado is not None:
            try:
                return int(guardado)
            except (TypeError, ValueError):
                pass
    return None


def resolver_sesion_kinesica(paciente, numero_sesion=None):
    qs = SesionKinesica.objects.filter(paciente=paciente)
    if numero_sesion is not None:
        return qs.filter(numero_sesion=numero_sesion).first()
    return qs.order_by('-numero_sesion').first()


def registrar_escala_aplicada(paciente, tipo_escala, resumen, url_name='', numero_sesion=None, request=None):
    """
    Registra que se aplicó una escala en una sesión kinésica.
    Si no hay numero_sesion, usa la última sesión del paciente.
    Si no hay sesiones, no registra nada.
    """
    if request is not None and numero_sesion is None:
        numero_sesion = numero_sesion_desde_request(request, paciente.rut)

    sesion = resolver_sesion_kinesica(paciente, numero_sesion)
    if not sesion:
        return None

    resumen = (resumen or '').strip()[:255]
    if not resumen:
        return None

    return RegistroEscalaSesion.objects.create(
        paciente=paciente,
        sesion_kinesica=sesion,
        tipo_escala=tipo_escala,
        resumen=resumen,
        url_name=(url_name or '')[:40],
    )


def obtener_escalas_agrupadas_por_numero(paciente):
    """Dict numero_sesion → lista de RegistroEscalaSesion."""
    registros = (
        RegistroEscalaSesion.objects.filter(paciente=paciente)
        .select_related('sesion_kinesica')
        .order_by('-fecha_registro')
    )
    agrupado = {}
    for reg in registros:
        num = reg.sesion_kinesica.numero_sesion
        agrupado.setdefault(num, []).append(reg)
    return agrupado


def anotar_escalas_en_sesiones(paciente, sesiones):
    agrupado = obtener_escalas_agrupadas_por_numero(paciente)
    for sesion in sesiones:
        sesion.escalas_en_sesion = agrupado.get(sesion.numero_sesion, [])
    return agrupado


def urls_escalas_para_sesion(paciente_rut, numero_sesion):
    """Enlaces para aplicar escalas vinculadas a una sesión."""
    items = []
    for codigo, nombre, url_name, descripcion in ESCALAS_MENU:
        items.append({
            'codigo': codigo,
            'nombre': nombre,
            'descripcion': descripcion,
            'url': f"{reverse(url_name)}?rut={paciente_rut}&numero_sesion={numero_sesion}",
        })
    return items
