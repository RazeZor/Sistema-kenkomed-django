from django.core.exceptions import ObjectDoesNotExist
from planes.models import SuscripcionClinica

def obtener_suscripcion_activa(clinica):
    """Retorna la suscripción activa de una clínica o None."""
    try:
        return SuscripcionClinica.objects.get(clinica=clinica, estado='activa')
    except ObjectDoesNotExist:
        return None

def verificar_limite_kinesiologos(clinica):
    """
    Verifica si la clínica puede agregar un nuevo kinesiólogo según su plan.
    Retorna True si puede agregarlo, False si superó el límite.
    """
    suscripcion = obtener_suscripcion_activa(clinica)
    if not suscripcion:
        return True # Sin plan, se asume legacy o fallback

    # Limite infinito
    if suscripcion.plan.max_kinesiologos == -1:
        return True
        
    from clinicas.models import MembresiaClinica
    miembros_activos = MembresiaClinica.objects.filter(clinica=clinica, activo=True).count()
    
    return miembros_activos < suscripcion.plan.max_kinesiologos

def verificar_limite_pacientes(clinica):
    """
    Verifica si la clínica puede agregar un nuevo paciente según su plan.
    Retorna True si puede agregarlo, False si superó el límite.
    """
    suscripcion = obtener_suscripcion_activa(clinica)
    if not suscripcion:
        return True
        
    if suscripcion.plan.max_pacientes_activos == -1:
        return True
        
    from Login.models import Paciente
    pacientes_activos = Paciente.objects.filter(clinica=clinica).count() # Puede requerir filtro de "activo" según reglas
    
    return pacientes_activos < suscripcion.plan.max_pacientes_activos
