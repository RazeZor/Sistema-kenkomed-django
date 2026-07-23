"""Contexto UX para flujo de tratamiento kinésico (ciclos + sesiones)."""
from datetime import date

from django.urls import reverse
from django.utils import timezone

from ciclos_clinicos.selectors import listar_ciclos_paciente


def _url_listar(rut, ciclo):
    url = f"{reverse('sesiones_kinesicas:listar')}?rut={rut}"
    if ciclo:
        url += f'&ciclo_id={ciclo.id}'
    return url


def _url_crear(rut, ciclo, vista):
    url = f"{reverse(f'sesiones_kinesicas:{vista}')}?rut={rut}"
    if ciclo:
        url += f'&ciclo_id={ciclo.id}'
    return url


def _url_ver(rut, ciclo, numero_sesion):
    url = f"{reverse('sesiones_kinesicas:ver')}?rut={rut}&numero_sesion={numero_sesion}"
    if ciclo:
        url += f'&ciclo_id={ciclo.id}'
    return url


def _dias_desde(fecha_dt):
    if not fecha_dt:
        return None
    hoy = timezone.localdate()
    ref = fecha_dt.date() if hasattr(fecha_dt, 'date') else fecha_dt
    if isinstance(ref, date):
        return (hoy - ref).days
    return None


def _estado_stepper(tiene_inicial, en_tratamiento, tiene_alta):
    if not tiene_inicial:
        return {
            'inicial': 'current',
            'seguimiento': 'pending',
            'alta': 'pending',
        }
    if tiene_alta:
        return {
            'inicial': 'done',
            'seguimiento': 'done',
            'alta': 'done',
        }
    if en_tratamiento:
        return {
            'inicial': 'done',
            'seguimiento': 'current',
            'alta': 'pending',
        }
    return {
        'inicial': 'done',
        'seguimiento': 'pending',
        'alta': 'pending',
    }


def contexto_tratamiento_ux(request, paciente, ciclo, sesiones_qs):
    """
    Arma contexto de guía clínica: fase, stepper, CTAs y selector de tratamientos.
    """
    clinica_id = request.session.get('clinica_id') if request else None
    ciclos_historial = list(listar_ciclos_paciente(paciente, clinica_id)) if paciente else []

    if not ciclo:
        return {
            'ciclos_historial': ciclos_historial,
            'ultima_sesion': None,
            'tratamiento_ux': None,
        }

    rut = paciente.rut
    tiene_inicial = sesiones_qs.filter(es_primera_sesion=True).exists()
    tiene_alta = sesiones_qs.filter(es_sesion_final=True).exists()
    solo_lectura = ciclo.es_solo_lectura
    en_tratamiento = tiene_inicial and not tiene_alta and not solo_lectura

    ultima_sesion = sesiones_qs.order_by('-numero_sesion').first()
    total = sesiones_qs.count()
    seguimientos = sesiones_qs.filter(
        es_primera_sesion=False, es_sesion_final=False,
    ).count()
    dias_ultima = _dias_desde(ultima_sesion.fecha_creacion) if ultima_sesion else None

    if solo_lectura or tiene_alta:
        fase = 'cerrado'
    elif not tiene_inicial:
        fase = 'sin_inicial'
    else:
        fase = 'en_tratamiento'

    resumen_partes = [
        f'Tratamiento #{ciclo.numero_ciclo}',
        ciclo.get_estado_display().lower(),
    ]
    if total:
        resumen_partes.append(f'{total} sesión{"es" if total != 1 else ""}')
    if tiene_alta:
        resumen_partes.append('alta registrada')
    elif tiene_inicial and not solo_lectura:
        resumen_partes.append('sin alta')

    if fase == 'sin_inicial':
        mensaje = 'Comience con la evaluación inicial para abrir el seguimiento kinésico.'
    elif fase == 'en_tratamiento':
        if dias_ultima is not None and dias_ultima == 0:
            mensaje = 'Tratamiento en curso. Puede registrar la sesión de hoy o revisar la última atención.'
        elif dias_ultima is not None and dias_ultima > 0:
            mensaje = (
                f'Última atención hace {dias_ultima} día{"s" if dias_ultima != 1 else ""}. '
                'Registre la sesión de hoy cuando atienda al paciente.'
            )
        else:
            mensaje = 'Tratamiento en curso. Registre cada sesión de seguimiento desde aquí.'
    else:
        mensaje = 'Este tratamiento está cerrado. Los datos son de solo lectura.'

    cta_primario = None
    cta_secundario = None

    if fase == 'sin_inicial' and not solo_lectura:
        cta_primario = {
            'url': _url_crear(rut, ciclo, 'crear_primera'),
            'label': 'Evaluación inicial',
            'icon': 'bx-plus-medical',
        }
    elif fase == 'en_tratamiento':
        cta_primario = {
            'url': _url_crear(rut, ciclo, 'crear_seguimiento'),
            'label': 'Registrar sesión de hoy',
            'icon': 'bx-plus',
        }
        cta_secundario = {
            'url': _url_crear(rut, ciclo, 'crear_final'),
            'label': 'Cerrar tratamiento (alta)',
            'icon': 'bx-check',
            'confirm': (
                '¿Confirma el cierre del tratamiento?\n\n'
                'Se registrará la sesión de alta y este episodio quedará en solo lectura.'
            ),
        }
    elif ultima_sesion:
        cta_primario = {
            'url': _url_ver(rut, ciclo, ultima_sesion.numero_sesion),
            'label': 'Ver última sesión',
            'icon': 'bx-show',
        }

    tratamiento_ux = {
        'fase': fase,
        'resumen': ' · '.join(resumen_partes),
        'mensaje_guia': mensaje,
        'tiene_inicial': tiene_inicial,
        'tiene_alta': tiene_alta,
        'en_tratamiento': en_tratamiento,
        'total_sesiones': total,
        'sesiones_seguimiento': seguimientos,
        'dias_desde_ultima': dias_ultima,
        'stepper': _estado_stepper(tiene_inicial, en_tratamiento, tiene_alta),
        'cta_primario': cta_primario,
        'cta_secundario': cta_secundario,
        'url_listar': _url_listar(rut, ciclo),
    }

    return {
        'ciclos_historial': ciclos_historial,
        'ultima_sesion': ultima_sesion,
        'tratamiento_ux': tratamiento_ux,
    }
