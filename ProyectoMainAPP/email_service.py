"""
Servicio centralizado de notificaciones por correo electrónico.
Todas las funciones son fire-and-forget: si falla el envío, se registra
en el log pero NO interrumpe el flujo de la aplicación.
"""
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _enviar_correo(asunto, plantilla, contexto, destinatarios):
    """
    Función interna para enviar un correo con plantilla HTML.
    - asunto: str con el asunto del correo
    - plantilla: ruta a la plantilla HTML (ej: 'emails/nuevo_paciente.html')
    - contexto: dict con variables para la plantilla
    - destinatarios: lista de correos electrónicos
    """
    # Filtrar destinatarios vacíos o None
    destinatarios = [d for d in destinatarios if d]
    if not destinatarios:
        logger.info(f"No se envió correo '{asunto}': sin destinatarios con email.")
        return False

    try:
        # Agregar datos comunes al contexto
        contexto['nombre_sistema'] = 'KenkoMed'
        contexto['correo_contacto'] = getattr(settings, 'DEFAULT_FROM_EMAIL', 'kenkomedplus@gmail.com')

        # Renderizar plantilla HTML
        html_content = render_to_string(plantilla, contexto)
        text_content = strip_tags(html_content)  # Versión texto plano como fallback

        # Crear y enviar el correo
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'kenkomedplus@gmail.com'),
            to=destinatarios,
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        logger.info(f"Correo enviado: '{asunto}' → {destinatarios}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo '{asunto}' a {destinatarios}: {str(e)}")
        return False


# ============================================================
# FUNCIONES PÚBLICAS DE NOTIFICACIÓN
# ============================================================

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

    # Correo al paciente
    _enviar_correo(
        asunto='Bienvenido a KenkoMed — Registro exitoso',
        plantilla='emails/nuevo_paciente.html',
        contexto={**contexto, 'es_paciente': True},
        destinatarios=[getattr(paciente, 'correo', None)],
    )

    # Correo al clínico
    _enviar_correo(
        asunto=f'Nuevo paciente registrado: {paciente.nombre} {paciente.apellido}',
        plantilla='emails/nuevo_paciente.html',
        contexto={**contexto, 'es_paciente': False},
        destinatarios=[getattr(clinico, 'correo', None)],
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
        asunto=f'Formulario completado: {paciente.nombre} {paciente.apellido}',
        plantilla='emails/formulario_completado.html',
        contexto=contexto,
        destinatarios=[getattr(clinico, 'correo', None)],
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

    # Correo al paciente
    _enviar_correo(
        asunto='Resumen de tu alta — KenkoMed',
        plantilla='emails/alta_paciente.html',
        contexto={**contexto, 'es_paciente': True},
        destinatarios=[getattr(paciente, 'correo', None)],
    )

    # Correo al clínico
    _enviar_correo(
        asunto=f'Alta registrada: {paciente.nombre} {paciente.apellido}',
        plantilla='emails/alta_paciente.html',
        contexto={**contexto, 'es_paciente': False},
        destinatarios=[getattr(clinico, 'correo', None)],
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
        'fecha': reserva.fecha.strftime('%d/%m/%Y') if reserva.fecha else '',
        'hora_inicio': reserva.hora_inicio.strftime('%H:%M') if reserva.hora_inicio else '',
        'hora_fin': reserva.hora_fin.strftime('%H:%M') if reserva.hora_fin else '',
        'motivo': reserva.motivo or '',
    }

    _enviar_correo(
        asunto='Confirmación de cita — KenkoMed',
        plantilla='emails/reserva_creada.html',
        contexto=contexto,
        destinatarios=[getattr(paciente, 'correo', None)],
    )
