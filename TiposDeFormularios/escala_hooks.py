"""Registra escalas aplicadas y mantiene el vínculo con sesiones kinésicas."""
from django.urls import reverse

from SesionesKinesicas.escalas_sesion import numero_sesion_desde_request, registrar_escala_aplicada


def sincronizar_numero_sesion_kine(request, paciente):
    if paciente:
        return numero_sesion_desde_request(request, paciente.rut)
    return None


def vincular_escala_a_sesion(request, paciente, tipo_escala, resumen, url_name=''):
    return registrar_escala_aplicada(
        paciente,
        tipo_escala,
        resumen,
        url_name=url_name,
        request=request,
    )


def redirect_cuestionario(request, url_name, rut):
    url = f"{reverse(url_name)}?rut={rut}"
    numero = numero_sesion_desde_request(request, rut)
    if numero:
        url += f'&numero_sesion={numero}'
    from django.shortcuts import redirect
    return redirect(url)
