"""Registro de accesos a datos sensibles de pacientes (Ley 21.719)."""
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


def registrar_acceso(request, paciente, accion):
    """Registra quién accedió a datos clínicos de un paciente."""
    if not paciente:
        return
    clinico = _clinico_desde_sesion(request)
    clinica_id = request.session.get('clinica_id')
    if not clinica_id and paciente.clinica_id:
        clinica_id = paciente.clinica_id
    AuditoriaAcceso.objects.create(
        paciente=paciente,
        clinico=clinico,
        clinica_id=clinica_id,
        accion=accion,
        ip_address=obtener_ip_cliente(request),
    )
