"""Registro de accesos y cambios sobre datos sensibles (Ley 21.719)."""
from Login.models import AuditoriaAcceso, Clinico


def obtener_ip_cliente(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR') or None


def _clinico_desde_sesion(request):
    rut = request.session.get('rut_clinico')
    if not rut:
        return None
    return Clinico.objects.filter(rut=rut).first()


def registrar_auditoria(request, accion, paciente=None, detalle=''):
    """Registra una acción clínica realizada por el usuario en sesión."""
    clinico = _clinico_desde_sesion(request)
    clinica_id = request.session.get('clinica_id')
    if not clinica_id and paciente and paciente.clinica_id:
        clinica_id = paciente.clinica_id

    AuditoriaAcceso.objects.create(
        paciente=paciente,
        clinico=clinico,
        clinica_id=clinica_id,
        accion=accion,
        detalle=(detalle or '').strip()[:500],
        es_admin_sistema=bool(request.session.get('es_admin')),
        es_admin_centro=bool(request.session.get('es_admin_clinica')),
        ip_address=obtener_ip_cliente(request),
    )


def registrar_acceso(request, paciente, accion, detalle=''):
    """Alias retrocompatible; preferir registrar_auditoria."""
    registrar_auditoria(request, accion, paciente=paciente, detalle=detalle)
