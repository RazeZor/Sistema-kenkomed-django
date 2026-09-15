from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect


def requiere_feature(feature_name):
    """
    Decorador para proteger vistas según las capacidades del plan de la clínica activa.
    Si la cuenta es legacy o admin del sistema, se permite el acceso total.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.session.get('es_admin'):
                return view_func(request, *args, **kwargs)

            clinica_id = request.session.get('clinica_id')
            if not clinica_id:
                messages.error(request, 'No tienes una clínica activa en sesión.')
                return redirect('login')

            from clinicas.models import Clinica
            clinica = Clinica.objects.filter(id=clinica_id, activa=True).first()
            if not clinica:
                messages.error(request, 'Clínica no encontrada o inactiva.')
                return redirect('panel')

            suscripcion = getattr(clinica, 'suscripcion', None)
            if not suscripcion:
                # Si la clínica no tiene registro explícito de suscripción todavía, se asume legacy
                return view_func(request, *args, **kwargs)

            if suscripcion.tiene_feature(feature_name):
                return view_func(request, *args, **kwargs)

            messages.warning(
                request,
                'Tu plan actual no incluye acceso a esta funcionalidad. '
                'Contacta a soporte o actualiza tu plan para habilitarla.'
            )
            return redirect('panel')
        return _wrapped_view
    return decorator
