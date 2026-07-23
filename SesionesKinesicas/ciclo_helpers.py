"""Helpers compartidos para vistas de sesiones kinésicas."""
from django.urls import reverse

from ciclos_clinicos.services import (
    CicloClinicoError,
    asegurar_ciclo_editable,
    finalizar_ciclo,
    obtener_ciclo_desde_request,
)


def resolver_ciclo(request, paciente, clinico=None, crear_si_ausente=False):
    return obtener_ciclo_desde_request(
        request, paciente, crear_si_ausente=crear_si_ausente, clinico=clinico,
    )


def asegurar_editable(request, ciclo):
    try:
        asegurar_ciclo_editable(ciclo)
        return True
    except CicloClinicoError as exc:
        from django.contrib import messages
        messages.error(request, str(exc))
        return False


def filtrar_sesiones(ciclo, ascendente=False):
    from .models import SesionKinesica
    orden = 'numero_sesion' if ascendente else '-numero_sesion'
    return SesionKinesica.objects.filter(ciclo=ciclo).order_by(orden)


def redirect_listar(rut, ciclo=None):
    url = f"{reverse('sesiones_kinesicas:listar')}?rut={rut}"
    if ciclo:
        url += f'&ciclo_id={ciclo.id}'
    return url


def redirect_ver(rut, numero_sesion, ciclo=None):
    url = f"{reverse('sesiones_kinesicas:ver')}?rut={rut}&numero_sesion={numero_sesion}"
    if ciclo:
        url += f'&ciclo_id={ciclo.id}'
    return url


def finalizar_ciclo_si_sesion_final(request, sesion, clinico):
    if sesion.es_sesion_final and sesion.ciclo_id:
        finalizar_ciclo(sesion.ciclo, clinico=clinico, request=request)
