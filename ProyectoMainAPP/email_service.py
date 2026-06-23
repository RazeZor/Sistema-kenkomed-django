"""
Servicio centralizado de notificaciones por correo electrónico.
Todas las funciones son fire-and-forget: si falla el envío, se registra
en el log pero NO interrumpe el flujo de la aplicación.
"""
import logging
from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import datetime, date, time

from clinicas.branding import resolver_branding_correo, tipo_mime_logo

logger = logging.getLogger(__name__)


def _formatear_fecha(valor, formato):
    """
    Convierte de forma segura un valor (str o date/time) al formato indicado.
    Evita el error 'str object has no attribute strftime'.
    """
    if not valor:
        return ''
    if isinstance(valor, str):
        try:
            # Intenta parsear como fecha ISO (YYYY-MM-DD)
            if len(valor) == 10 and '-' in valor:
                return datetime.strptime(valor, '%Y-%m-%d').strftime(formato)
            # Intenta parsear como hora HH:MM o HH:MM:SS
            if ':' in valor:
                hora = valor[:5]  # Tomar solo HH:MM
                return datetime.strptime(hora, '%H:%M').strftime(formato)
        except Exception:
            return valor  # Si no puede parsear, devuelve el string tal cual
        return valor
    try:
        return valor.strftime(formato)
    except Exception:
        return str(valor)


def _enviar_correo(asunto, plantilla, contexto, destinatarios, clinica=None):
    """
    Función interna para enviar un correo con plantilla HTML.
    - asunto: str con el asunto del correo
    - plantilla: ruta a la plantilla HTML (ej: 'emails/nuevo_paciente.html')
    - contexto: dict con variables para la plantilla
    - destinatarios: lista de correos electrónicos
    - clinica: instancia Clinica opcional para logo y nombre del centro
    """
    # Filtrar destinatarios vacíos o None
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        logger.info(f"No se envió correo '{asunto}': sin destinatarios con email.")
        return False

    try:
        branding = resolver_branding_correo(clinica)
        contexto['nombre_sistema'] = 'KenkoMed'
        contexto['correo_contacto'] = getattr(settings, 'DEFAULT_FROM_EMAIL', 'kenkomedplus@gmail.com')
        contexto['nombre_marca'] = branding['nombre_marca']
        contexto['es_marca_clinica'] = branding['es_marca_clinica']
        contexto['tiene_logo'] = branding['tiene_logo']
        contexto['logo_cid'] = branding['logo_cid']

        html_content = render_to_string(plantilla, contexto)
        marca_visible = branding['nombre_marca']
        text_content = (
            f"{asunto}\n\n"
            f"Ha recibido una notificación de {marca_visible}. "
            "Abra este correo en un cliente compatible con HTML para ver el contenido completo.\n\n"
            f"KenkoMed — {contexto['correo_contacto']}"
        )

        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'kenkomedplus@gmail.com'),
            to=destinatarios,
        )
        email.attach_alternative(html_content, 'text/html')

        ruta_logo = branding.get('logo_ruta')
        if branding['tiene_logo'] and ruta_logo and Path(ruta_logo).exists():
            try:
                imagen = MIMEImage(ruta_logo.read_bytes(), _subtype=tipo_mime_logo(ruta_logo).split('/')[-1])
                imagen.add_header('Content-ID', f'<{branding["logo_cid"]}>')
                imagen.add_header('Content-Disposition', 'inline', filename=branding['logo_filename'])
                email.attach(imagen)
                email.mixed_subtype = 'related'
            except OSError as e:
                logger.warning(f'No se pudo adjuntar el logo al correo: {e}')
        email.send(fail_silently=False)

        logger.info(f"Correo enviado: '{asunto}' → {destinatarios}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo '{asunto}' a {destinatarios}: {str(e)}")
        return False


# ============================================================
# FUNCIONES PÚBLICAS DE NOTIFICACIÓN
# ============================================================

def _clinica_de_paciente(paciente):
    return getattr(paciente, 'clinica', None)


def notificar_nuevo_paciente(paciente, clinico):
    """
    Envía correo de bienvenida al paciente y aviso al clínico
    cuando se registra un nuevo paciente en el sistema.
    """
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'paciente_rut': paciente.rut,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
        'clinico_profesion': clinico.profesion,
    }

    clinica = _clinica_de_paciente(paciente)

    # Correo al paciente
    _enviar_correo(
        asunto='Bienvenido a KenkoMed — Registro exitoso',
        plantilla='emails/nuevo_paciente.html',
        contexto={**contexto, 'es_paciente': True},
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=clinica,
    )

    # Correo al clínico
    _enviar_correo(
        asunto='Nuevo paciente registrado — KenkoMed',
        plantilla='emails/nuevo_paciente.html',
        contexto={**contexto, 'es_paciente': False},
        destinatarios=[getattr(clinico, 'correo', None)],
        clinica=clinica,
    )


def notificar_formulario_completado(paciente, clinico):
    """
    Notifica al clínico cuando un paciente completa el formulario
    de anamnesis remoto (vía QR/link).
    """
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'paciente_rut': paciente.rut,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
    }

    _enviar_correo(
        asunto='Formulario de anamnesis completado — KenkoMed',
        plantilla='emails/formulario_completado.html',
        contexto=contexto,
        destinatarios=[getattr(clinico, 'correo', None)],
        clinica=_clinica_de_paciente(paciente),
    )


def notificar_receta_creada(paciente, clinico, receta):
    """
    Notifica al paciente cuando se le crea una receta médica.
    """
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
        'clinico_profesion': clinico.profesion,
        'medicamentos': receta.medicamentos or '',
        'indicaciones': receta.indicaciones or '',
        'notas': receta.NotaRecetaMedica or '',
    }

    _enviar_correo(
        asunto='Nueva receta médica — KenkoMed',
        plantilla='emails/receta_creada.html',
        contexto=contexto,
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=_clinica_de_paciente(paciente),
    )


def notificar_receta_actualizada(paciente, receta):
    """
    Notifica al paciente cuando su receta médica es actualizada.
    """
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'medicamentos': receta.medicamentos or '',
        'indicaciones': receta.indicaciones or '',
        'notas': receta.NotaRecetaMedica or '',
    }

    _enviar_correo(
        asunto='Tu receta médica ha sido actualizada — KenkoMed',
        plantilla='emails/receta_actualizada.html',
        contexto=contexto,
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=_clinica_de_paciente(paciente),
    )


def notificar_alta_paciente(paciente, clinico, sesion):
    """
    Notifica al paciente y clínico cuando se registra el alta
    (sesión final del tratamiento kinésico).
    """
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'paciente_rut': paciente.rut,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
        'clinico_profesion': clinico.profesion,
        'numero_sesion': sesion.numero_sesion,
        'diagnostico_final': sesion.diagnostico_final or '',
        'resumen_tratamiento': sesion.resumen_tratamiento or '',
        'logros_obtenidos': sesion.logros_obtenidos or '',
        'estado_al_alta': sesion.get_estado_al_alta_display() if sesion.estado_al_alta else '',
        'recomendaciones_alta': sesion.recomendaciones_alta or '',
        'plan_seguimiento': sesion.plan_seguimiento or '',
    }

    clinica = _clinica_de_paciente(paciente)

    # Correo al paciente
    _enviar_correo(
        asunto='Resumen de tu alta — KenkoMed',
        plantilla='emails/alta_paciente.html',
        contexto={**contexto, 'es_paciente': True},
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=clinica,
    )

    # Correo al clínico
    _enviar_correo(
        asunto='Alta de paciente registrada — KenkoMed',
        plantilla='emails/alta_paciente.html',
        contexto={**contexto, 'es_paciente': False},
        destinatarios=[getattr(clinico, 'correo', None)],
        clinica=clinica,
    )


def notificar_reserva_creada(paciente, clinico, reserva):
    """
    Notifica al paciente cuando se crea una reserva de cita.
    """
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
        'clinico_profesion': clinico.profesion,
        'fecha': _formatear_fecha(reserva.fecha, '%d/%m/%Y'),
        'hora_inicio': _formatear_fecha(reserva.hora_inicio, '%H:%M'),
        'hora_fin': _formatear_fecha(reserva.hora_fin, '%H:%M'),
        'motivo': reserva.motivo or '',
    }

    _enviar_correo(
        asunto='Confirmación de cita — KenkoMed',
        plantilla='emails/reserva_creada.html',
        contexto=contexto,
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=_clinica_de_paciente(paciente),
    )


def notificar_reserva_reagendada(paciente, clinico, reserva):
    """Notifica al paciente cuando su cita es reagendada."""
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
        'clinico_profesion': clinico.profesion,
        'fecha': _formatear_fecha(reserva.fecha, '%d/%m/%Y'),
        'hora_inicio': _formatear_fecha(reserva.hora_inicio, '%H:%M'),
        'hora_fin': _formatear_fecha(reserva.hora_fin, '%H:%M'),
    }

    _enviar_correo(
        asunto='Cambio de horario de cita — KenkoMed',
        plantilla='emails/reserva_reagendada.html',
        contexto=contexto,
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=_clinica_de_paciente(paciente),
    )


def notificar_reserva_cancelada(paciente, clinico, fecha, hora_inicio):
    """Notifica al paciente cuando su cita es cancelada."""
    contexto = {
        'paciente_nombre': paciente.nombre,
        'paciente_apellido': paciente.apellido,
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}",
        'clinico_profesion': clinico.profesion,
        'fecha': _formatear_fecha(fecha, '%d/%m/%Y'),
        'hora_inicio': _formatear_fecha(hora_inicio, '%H:%M'),
    }

    _enviar_correo(
        asunto='Cancelación de cita — KenkoMed',
        plantilla='emails/reserva_cancelada.html',
        contexto=contexto,
        destinatarios=[getattr(paciente, 'correo', None)],
        clinica=_clinica_de_paciente(paciente),
    )
