"""Vistas personalizadas de error HTTP — KenkoMed."""
from django.conf import settings
from django.shortcuts import render

ERROR_CONFIG = {
    400: {
        'title': 'Solicitud incorrecta',
        'subtitle': (
            'Los datos enviados no son válidos o la petición está mal formada. '
            'Revise el formulario e intente nuevamente.'
        ),
        'icon': 'bx-error-circle',
        'accent': 'amber',
    },
    403: {
        'title': 'Acceso denegado',
        'subtitle': (
            'No tiene permisos para ver o realizar esta acción en KenkoMed. '
            'Si cree que es un error, contacte al administrador de su centro.'
        ),
        'icon': 'bx-shield-quarter',
        'accent': 'red',
    },
    404: {
        'title': 'Página no encontrada',
        'subtitle': (
            'La dirección que buscó no existe, fue movida o ya no está disponible '
            'en el sistema clínico.'
        ),
        'icon': 'bx-search-alt',
        'accent': 'blue',
    },
    500: {
        'title': 'Error interno del servidor',
        'subtitle': (
            'Ocurrió un problema inesperado al procesar su solicitud. '
            'Nuestro equipo puede revisar los registros del sistema.'
        ),
        'icon': 'bx-server',
        'accent': 'red',
    },
    503: {
        'title': 'Servicio no disponible',
        'subtitle': (
            'KenkoMed no está disponible temporalmente por mantenimiento o alta demanda. '
            'Por favor, intente de nuevo en unos minutos.'
        ),
        'icon': 'bx-wrench',
        'accent': 'orange',
    },
}


def _render_error(request, status_code, extra=None):
    config = ERROR_CONFIG.get(status_code, ERROR_CONFIG[500]).copy()
    if extra:
        config.update(extra)

    context = {
        'status_code': status_code,
        'title': config['title'],
        'subtitle': config['subtitle'],
        'icon': config['icon'],
        'accent': config['accent'],
        'tiene_sesion': bool(request.session.get('nombre_clinico')),
        'detail': config.get('detail', ''),
        'show_detail': bool(settings.DEBUG and config.get('detail')),
    }
    return render(request, 'errors/page.html', context, status=status_code)


def handler400(request, exception=None):
    detail = str(exception) if exception and settings.DEBUG else ''
    return _render_error(request, 400, {'detail': detail})


def handler403(request, exception=None):
    detail = str(exception) if exception and settings.DEBUG else ''
    return _render_error(request, 403, {'detail': detail})


def handler404(request, exception=None):
    detail = str(exception) if exception and settings.DEBUG else ''
    return _render_error(request, 404, {'detail': detail})


def handler500(request):
    return _render_error(request, 500)


def handler503(request, exception=None):
    detail = str(exception) if exception and settings.DEBUG else ''
    return _render_error(request, 503, {'detail': detail})


def csrf_failure(request, reason=''):
    detail = reason if settings.DEBUG else ''
    extra = {
        'title': 'Sesión de seguridad expirada',
        'subtitle': (
            'El formulario tardó demasiado o la sesión de seguridad caducó. '
            'Recargue la página e intente nuevamente.'
        ),
        'icon': 'bx-lock-alt',
        'accent': 'amber',
        'detail': detail,
    }
    return _render_error(request, 403, extra)


def preview_error(request, code):
    """Vista de prueba de páginas de error (solo DEBUG)."""
    mapping = {
        400: handler400,
        403: handler403,
        404: handler404,
        500: handler500,
        503: handler503,
    }
    handler = mapping.get(code, handler404)
    if code == 500:
        return handler(request)
    return handler(request, Exception('Vista de prueba de error KenkoMed'))
