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
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        if request.session.get('es_admin'):
            return view_func(request, *args, **kwargs)
        if not request.session.get('es_admin_clinica'):
            messages.error(request, 'No tienes permisos de administrador de clínica.')
            return redirect('panel')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
