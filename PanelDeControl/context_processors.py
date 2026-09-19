from Login.models import Clinico
from .novedades import VERSION_ACTUAL, NOVEDADES_HISTORIAL

def novedades_processor(request):
    """
    Inyecta en el contexto global si hay novedades sin leer para el usuario,
    la versión actual y el historial completo de novedades.
    """
    # Solo aplica si hay un usuario autenticado (con rut en sesión)
    rut_clinico = request.session.get('rut_clinico')
    
    hay_novedades = False
    
    if rut_clinico:
        # Recuperar clinico y comparar versiones
        clinico = Clinico.objects.filter(rut=rut_clinico).first()
        if clinico and clinico.version_novedades_leida != VERSION_ACTUAL:
            hay_novedades = True

    return {
        'hay_novedades': hay_novedades,
        'version_novedades_actual': VERSION_ACTUAL,
        'historial_novedades': NOVEDADES_HISTORIAL,
        'novedades_recientes': NOVEDADES_HISTORIAL[0] if NOVEDADES_HISTORIAL else None
    }
