"""Vincula escalas/cuestionarios clínicos con sesiones kinésicas."""
from django.urls import reverse

from .models import RegistroEscalaSesion, SesionKinesica

ESCALAS_POR_CODIGO = {
    'psfs': ('PSFS', 'gestionar_psfs', 'Función específica del paciente (0–10)'),
    'groc': ('GROC', 'GROK', 'Cambio global percibido'),
    'eq5d': ('EQ-5D', 'EQ_5D', 'Calidad de vida y escala visual analógica'),
    'barthel': ('Barthel', 'bartel', 'Autonomía en actividades diarias'),
    'ena': ('ENA', 'ENA', 'Intensidad del dolor (0–10)'),
    'screening': ('Screening Örebro', 'Screnning', 'Riesgo de cronificación'),
    'oswestry': ('Oswestry ODI', 'oswestry', 'Incapacidad por dolor lumbar'),
    'lefs': ('LEFS', 'lefs', 'Función de extremidad inferior'),
}

ESCALAS_PAQUETES = (
    {
        'id': 'dolor_seguimiento',
        'titulo': 'Dolor y seguimiento',
        'descripcion': 'Lo más usado en cada sesión de control',
        'icono': 'bx-pulse',
        'escalas': ('ena', 'groc', 'psfs'),
    },
    {
        'id': 'columna_lumbar',
        'titulo': 'Columna lumbar',
        'descripcion': 'Pacientes con dolor lumbar o lumbociática',
        'icono': 'bx-body',
        'escalas': ('oswestry', 'screening'),
    },
    {
        'id': 'extremidad_inferior',
        'titulo': 'Extremidad inferior',
        'descripcion': 'Rodilla, cadera, tobillo y marcha',
        'icono': 'bx-run',
        'escalas': ('lefs',),
    },
    {
        'id': 'calidad_vida',
        'titulo': 'Calidad de vida y autonomía',
        'descripcion': 'Bienestar global y actividades cotidianas',
        'icono': 'bx-heart',
        'escalas': ('eq5d', 'barthel'),
    },
)

# Compatibilidad con código que usaba la tupla plana
ESCALAS_MENU = tuple(
    (codigo, meta[0], meta[1], meta[2])
    for codigo, meta in ESCALAS_POR_CODIGO.items()
)


def _item_escala(codigo, paciente_rut, numero_sesion=None):
    meta = ESCALAS_POR_CODIGO.get(codigo)
    if not meta:
        return None
    nombre, url_name, descripcion = meta
    url = f"{reverse(url_name)}?rut={paciente_rut}"
    if numero_sesion is not None:
        url += f'&numero_sesion={numero_sesion}'
    return {
        'codigo': codigo,
        'nombre': nombre,
        'descripcion': descripcion,
        'url': url,
    }


def paquetes_escalas_para_paciente(paciente_rut, numero_sesion=None):
    """Paquetes de escalas con título y enlaces listos para la UI."""
    paquetes = []
    for paquete in ESCALAS_PAQUETES:
        escalas = []
        for codigo in paquete['escalas']:
            item = _item_escala(codigo, paciente_rut, numero_sesion)
            if item:
                escalas.append(item)
        if escalas:
            paquetes.append({
                'id': paquete['id'],
                'titulo': paquete['titulo'],
                'descripcion': paquete['descripcion'],
                'icono': paquete.get('icono', 'bx-bar-chart-alt-2'),
                'escalas': escalas,
            })
    return paquetes


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
    """Lista plana de escalas (compatibilidad). Preferir paquetes_escalas_para_paciente."""
    items = []
    for paquete in paquetes_escalas_para_paciente(paciente_rut, numero_sesion):
        items.extend(paquete['escalas'])
    return items
