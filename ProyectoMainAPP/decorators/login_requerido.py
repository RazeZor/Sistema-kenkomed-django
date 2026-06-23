from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def requiere_clinico(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        if not request.session.get('es_admin') and not request.session.get('clinica_id'):
            messages.error(request, 'No tienes una clínica activa asociada.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def requiere_admin_clinica(view_func):
    """
    Solo administradores del centro activo (es_admin_clinica).
    El admin KenkoMed (es_admin) no usa estas vistas: gestiona desde Django Admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        if not request.session.get('es_admin_clinica'):
            messages.error(request, 'No tienes permisos de administrador de tu centro.')
            return redirect('panel')
        if not request.session.get('clinica_id'):
            messages.error(request, 'No tienes un centro activo asociado.')
            return redirect('panel')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def requiere_admin_auditoria(view_func):
    """Solo administradores del centro activo."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        if not request.session.get('clinica_id'):
            messages.error(request, 'Debes tener un centro activo para ver la auditoría.')
            return redirect('panel')
        if not request.session.get('es_admin_clinica'):
            messages.error(request, 'Solo los administradores del centro pueden consultar la auditoría.')
            return redirect('panel')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
