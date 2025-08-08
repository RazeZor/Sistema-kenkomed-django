# tu_app/decorators.py
from functools import wraps
from django.shortcuts import redirect

def requiere_clinico(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
