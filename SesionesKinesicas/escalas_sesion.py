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
    'quickdash': ('QuickDASH', 'quickdash', 'Discapacidad hombro, codo y mano'),
    'womac': ('WOMAC', 'womac', 'Artrosis rodilla/cadera: dolor, rigidez y función'),
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
        'escalas': ('lefs', 'womac'),
    },
    {
        'id': 'mmss_hombro',
        'titulo': 'Hombro, codo y mano',
        'descripcion': 'Discapacidad de extremidad superior',
        'icono': 'bx-hand',
        'escalas': ('quickdash',),
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


def _item_escala(codigo, paciente_rut, numero_sesion=None, ciclo_id=None):
    meta = ESCALAS_POR_CODIGO.get(codigo)
    if not meta:
        return None
    nombre, url_name, descripcion = meta
    url = f"{reverse(url_name)}?rut={paciente_rut}"
    if ciclo_id:
        url += f'&ciclo_id={ciclo_id}'
    if numero_sesion is not None:
        url += f'&numero_sesion={numero_sesion}'
    return {
        'codigo': codigo,
        'nombre': nombre,
        'descripcion': descripcion,
        'url': url,
    }


def paquetes_escalas_para_ciclo(paciente_rut, ciclo, numero_sesion=None):
    """Paquetes de escalas con enlaces scoped al ciclo clínico."""
    ciclo_id = ciclo.id if ciclo else None
    paquetes = []
    for paquete in ESCALAS_PAQUETES:
        escalas = []
        for codigo in paquete['escalas']:
            item = _item_escala(codigo, paciente_rut, numero_sesion, ciclo_id=ciclo_id)
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


def paquetes_escalas_para_paciente(paciente_rut, numero_sesion=None, ciclo=None):
    """Compatibilidad: delega en paquetes_escalas_para_ciclo si hay ciclo."""
    if ciclo:
        return paquetes_escalas_para_ciclo(paciente_rut, ciclo, numero_sesion)
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


def _session_key_escala(rut_paciente, ciclo_id=None):
    if ciclo_id:
        return f'escala_sesion_kine_{rut_paciente}_ciclo_{ciclo_id}'
    return f'escala_sesion_kine_{rut_paciente}'


def numero_sesion_desde_request(request, rut_paciente=None, ciclo_id=None):
    """Lee el número de sesión kinésica desde POST, GET o sesión Django."""
    if ciclo_id is None:
        ciclo_id = request.GET.get('ciclo_id') or request.POST.get('ciclo_id')
        if ciclo_id:
            try:
                ciclo_id = int(ciclo_id)
            except (TypeError, ValueError):
                ciclo_id = None

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
                request.session[_session_key_escala(rut_paciente, ciclo_id)] = numero
            return numero
        except (TypeError, ValueError):
            pass
    if rut_paciente:
        guardado = request.session.get(_session_key_escala(rut_paciente, ciclo_id))
        if guardado is None and ciclo_id:
            guardado = request.session.get(_session_key_escala(rut_paciente))
        if guardado is not None:
            try:
                return int(guardado)
            except (TypeError, ValueError):
                pass
    return None


def resolver_sesion_kinesica(paciente, numero_sesion=None, ciclo=None):
    if not ciclo:
        return None
    qs = SesionKinesica.objects.filter(ciclo=ciclo)
    if numero_sesion is not None:
        return qs.filter(numero_sesion=numero_sesion).first()
    return qs.order_by('-numero_sesion').first()


def registrar_escala_aplicada(paciente, tipo_escala, resumen, url_name='', numero_sesion=None, request=None, ciclo=None):
    """
    Registra que se aplicó una escala en una sesión kinésica.
    Si no hay numero_sesion, usa la última sesión del paciente.
    Si no hay sesiones, no registra nada.
    """
    if request is not None and ciclo is None:
        from ciclos_clinicos.services import obtener_ciclo_desde_request
        ciclo = obtener_ciclo_desde_request(request, paciente, crear_si_ausente=False)

    if request is not None and numero_sesion is None:
        ciclo_id = ciclo.id if ciclo else None
        numero_sesion = numero_sesion_desde_request(request, paciente.rut, ciclo_id=ciclo_id)

    sesion = resolver_sesion_kinesica(paciente, numero_sesion, ciclo=ciclo)
    if not sesion:
        return None

    resumen = (resumen or '').strip()[:255]
    if not resumen:
        return None

    return RegistroEscalaSesion.objects.create(
        paciente=paciente,
        ciclo=ciclo or sesion.ciclo,
        sesion_kinesica=sesion,
        tipo_escala=tipo_escala,
        resumen=resumen,
        url_name=(url_name or '')[:40],
    )


def obtener_escalas_agrupadas_por_numero(ciclo_or_paciente):
    """Dict numero_sesion → lista de RegistroEscalaSesion."""
    from ciclos_clinicos.models import CicloClinico
    if isinstance(ciclo_or_paciente, CicloClinico):
        filt = {'ciclo': ciclo_or_paciente}
    else:
        filt = {'paciente': ciclo_or_paciente}
    registros = (
        RegistroEscalaSesion.objects.filter(**filt)
        .select_related('sesion_kinesica')
        .order_by('-fecha_registro')
    )
    agrupado = {}
    for reg in registros:
        num = reg.sesion_kinesica.numero_sesion
        agrupado.setdefault(num, []).append(reg)
    return agrupado


def anotar_escalas_en_sesiones(ciclo_or_paciente, sesiones):
    agrupado = obtener_escalas_agrupadas_por_numero(ciclo_or_paciente)
    for sesion in sesiones:
        sesion.escalas_en_sesion = agrupado.get(sesion.numero_sesion, [])
    return agrupado


def urls_escalas_para_sesion(paciente_rut, numero_sesion):
    """Lista plana de escalas (compatibilidad). Preferir paquetes_escalas_para_paciente."""
    items = []
    for paquete in paquetes_escalas_para_paciente(paciente_rut, numero_sesion):
        items.extend(paquete['escalas'])
    return items
