from django.contrib import messages
from django.shortcuts import redirect, render

from ProyectoMainAPP.decorators.login_requerido import requiere_clinico

from .utils import obtener_clinica_de_sesion, obtener_membresias_del_centro


@requiere_clinico
def mi_centro(request):
    """Vista informativa: el equipo KenkoMed gestiona miembros desde Django Admin."""
    clinica = obtener_clinica_de_sesion(request)
    if not clinica and not request.session.get('es_admin'):
        messages.error(request, 'No tienes un centro asociado.')
        return redirect('panel')

    membresias = obtener_membresias_del_centro(request)

    return render(request, 'clinicas/mi_centro.html', {
        'clinica': clinica,
        'membresias': membresias,
        'total_miembros': membresias.count(),
        'nombre_clinico': request.session.get('nombre_clinico'),
        'es_centro_compartido': clinica and clinica.tipo == 'clinica',
        'es_admin_clinica': request.session.get('es_admin_clinica', False),
    })
