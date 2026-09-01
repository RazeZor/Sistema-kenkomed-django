"""
Servicio centralizado de notificaciones por correo electrónico.
Todas las funciones son fire-and-forget: si falla el envío, se registra
en el log pero NO interrumpe el flujo de la aplicación.
"""
import json
import logging
import threading
import urllib.request
import urllib.error
from email.mime.image import MIMEImage
from pathlib import Path
from datetime import datetime, date, time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import close_old_connections
from django.template.loader import render_to_string

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


def _ejecutar_en_background(func, *args, **kwargs):
    """
    Ejecuta una función en un hilo secundario en segundo plano,
    limpiando conexiones a la base de datos para evitar fallos en Uvicorn/Gunicorn.
    """
    def worker():
        close_old_connections()
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error en hilo de correo en segundo plano ({func.__name__}): {e}", exc_info=True)
        finally:
            close_old_connections()

    threading.Thread(target=worker, daemon=True).start()


def _enviar_correo(asunto, plantilla, contexto, destinatarios, clinica=None, bcc=None):
    """
    Función interna para enviar un correo con plantilla HTML.
    Prioriza el envío vía Resend API (HTTPS Puerto 443, inmune a bloqueos VPS).
    - asunto: str con el asunto del correo
    - plantilla: ruta a la plantilla HTML (ej: 'emails/nuevo_paciente.html')
    - contexto: dict con variables para la plantilla
    - destinatarios: lista de correos electrónicos
    - clinica: instancia Clinica opcional para logo y nombre del centro
    - bcc: lista o str opcional de copias ocultas
    """
    destinatarios = [d.strip() for d in destinatarios if d and isinstance(d, str) and d.strip()]
    if not destinatarios:
        logger.info(f"No se envió correo '{asunto}': sin destinatarios válidos con email.")
        return False

    try:
        branding = resolver_branding_correo(clinica)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'KenkoMed <kenkomedplus@gmail.com>')
        contexto['nombre_sistema'] = 'KenkoMed'
        contexto['correo_contacto'] = from_email
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
            f"KenkoMed — {from_email}"
        )

        # Copia oculta (BCC): incluir copia de respaldo del sistema (kenkomedplus@gmail.com)
        bcc_list = []
        if bcc:
            if isinstance(bcc, list):
                bcc_list.extend([b.strip() for b in bcc if b and isinstance(b, str) and b.strip()])
            elif isinstance(bcc, str) and bcc.strip():
                bcc_list.append(bcc.strip())

        copia_sistema = getattr(settings, 'EMAIL_BCC_SYSTEM', 'kenkomedplus@gmail.com')
        if copia_sistema and copia_sistema not in destinatarios and copia_sistema not in bcc_list:
            bcc_list.append(copia_sistema)

        # Intento de envío vía Resend API (HTTPS Puerto 443 - Inmune a bloqueos VPS/DigitalOcean)
        resend_api_key = getattr(settings, 'RESEND_API_KEY', '')
        if resend_api_key:
            try:
                resend_from = getattr(settings, 'RESEND_FROM_EMAIL', 'KenkoMed <onboarding@resend.dev>')
                payload = {
                    'from': resend_from,
                    'to': destinatarios,
                    'subject': asunto,
                    'html': html_content,
                }
                if bcc_list:
                    payload['bcc'] = bcc_list

                req = urllib.request.Request(
                    'https://api.resend.com/emails',
                    data=json.dumps(payload).encode('utf-8'),
                    headers={
                        'Authorization': f'Bearer {resend_api_key}',
                        'Content-Type': 'application/json',
                        'User-Agent': 'Resend/Python-SDK',
                    }
                )
                response = urllib.request.urlopen(req, timeout=10)
                res_data = json.loads(response.read().decode('utf-8'))
                logger.info(f"Correo enviado vía Resend API: '{asunto}' → Para: {destinatarios} | BCC: {bcc_list} | ID: {res_data.get('id')}")
                return True
            except urllib.error.HTTPError as e:
                body_err = e.read().decode('utf-8', errors='ignore')
                logger.error(f"Error HTTP en Resend API ({e.code}): {body_err}. Reintentando vía SMTP...", exc_info=True)
            except Exception as e:
                logger.error(f"Error al conectar con Resend API: {e}. Reintentando vía SMTP...", exc_info=True)

        # Respaldar vía SMTP tradicional
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=from_email,
            to=destinatarios,
            bcc=bcc_list if bcc_list else None,
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
        logger.info(f"Correo enviado vía SMTP: '{asunto}' → Para: {destinatarios} | BCC: {bcc_list}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar correo '{asunto}' a {destinatarios}: {str(e)}", exc_info=True)
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
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'paciente_rut': getattr(paciente, 'rut', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else '',
        'clinico_profesion': getattr(clinico, 'profesion', '') if clinico else '',
    }

    clinica = _clinica_de_paciente(paciente)

    # Correo al paciente
    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Bienvenido a KenkoMed — Registro exitoso',
            plantilla='emails/nuevo_paciente.html',
            contexto={**contexto, 'es_paciente': True},
            destinatarios=[paciente.correo],
            clinica=clinica,
        )

    # Correo al clínico
    if clinico and getattr(clinico, 'correo', None):
        _enviar_correo(
            asunto='Nuevo paciente registrado — KenkoMed',
            plantilla='emails/nuevo_paciente.html',
            contexto={**contexto, 'es_paciente': False},
            destinatarios=[clinico.correo],
            clinica=clinica,
        )


def notificar_formulario_completado(paciente, clinico):
    """
    Notifica al clínico y paciente cuando el paciente completa el formulario
    de anamnesis remoto (vía QR/link).
    """
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'paciente_rut': getattr(paciente, 'rut', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else '',
    }

    clinica = _clinica_de_paciente(paciente)

    if clinico and getattr(clinico, 'correo', None):
        _enviar_correo(
            asunto='Formulario de anamnesis completado — KenkoMed',
            plantilla='emails/formulario_completado.html',
            contexto=contexto,
            destinatarios=[clinico.correo],
            clinica=clinica,
        )


def notificar_receta_creada(paciente, clinico, receta):
    """
    Notifica al paciente cuando se le crea una receta médica.
    """
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else '',
        'clinico_profesion': getattr(clinico, 'profesion', '') if clinico else '',
        'medicamentos': getattr(receta, 'medicamentos', '') or '',
        'indicaciones': getattr(receta, 'indicaciones', '') or '',
        'notas': getattr(receta, 'NotaRecetaMedica', '') or '',
    }

    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Nueva receta médica — KenkoMed',
            plantilla='emails/receta_creada.html',
            contexto=contexto,
            destinatarios=[paciente.correo],
            clinica=_clinica_de_paciente(paciente),
        )


def notificar_receta_actualizada(paciente, receta):
    """
    Notifica al paciente cuando su receta médica es actualizada.
    """
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'medicamentos': getattr(receta, 'medicamentos', '') or '',
        'indicaciones': getattr(receta, 'indicaciones', '') or '',
        'notas': getattr(receta, 'NotaRecetaMedica', '') or '',
    }

    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Tu receta médica ha sido actualizada — KenkoMed',
            plantilla='emails/receta_actualizada.html',
            contexto=contexto,
            destinatarios=[paciente.correo],
            clinica=_clinica_de_paciente(paciente),
        )


def notificar_alta_paciente(paciente, clinico, sesion):
    """
    Notifica al paciente y clínico cuando se registra el alta
    (sesión final del tratamiento kinésico).
    """
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'paciente_rut': getattr(paciente, 'rut', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else '',
        'clinico_profesion': getattr(clinico, 'profesion', '') if clinico else '',
        'numero_sesion': getattr(sesion, 'numero_sesion', ''),
        'diagnostico_final': getattr(sesion, 'diagnostico_final', '') or '',
        'resumen_tratamiento': getattr(sesion, 'resumen_tratamiento', '') or '',
        'logros_obtenidos': getattr(sesion, 'logros_obtenidos', '') or '',
        'estado_al_alta': sesion.get_estado_al_alta_display() if hasattr(sesion, 'get_estado_al_alta_display') and sesion.estado_al_alta else '',
        'recomendaciones_alta': getattr(sesion, 'recomendaciones_alta', '') or '',
        'plan_seguimiento': getattr(sesion, 'plan_seguimiento', '') or '',
    }

    clinica = _clinica_de_paciente(paciente)

    # Correo al paciente
    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Resumen de tu alta — KenkoMed',
            plantilla='emails/alta_paciente.html',
            contexto={**contexto, 'es_paciente': True},
            destinatarios=[paciente.correo],
            clinica=clinica,
        )

    # Correo al clínico
    if clinico and getattr(clinico, 'correo', None):
        _enviar_correo(
            asunto='Alta de paciente registrada — KenkoMed',
            plantilla='emails/alta_paciente.html',
            contexto={**contexto, 'es_paciente': False},
            destinatarios=[clinico.correo],
            clinica=clinica,
        )


def notificar_reserva_creada(paciente, clinico, reserva):
    """
    Notifica al paciente y al clínico cuando se crea una reserva de cita.
    """
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else "Su profesional",
        'clinico_profesion': getattr(clinico, 'profesion', '') if clinico else '',
        'fecha': _formatear_fecha(getattr(reserva, 'fecha', None), '%d/%m/%Y'),
        'hora_inicio': _formatear_fecha(getattr(reserva, 'hora_inicio', None), '%H:%M'),
        'hora_fin': _formatear_fecha(getattr(reserva, 'hora_fin', None), '%H:%M'),
        'motivo': getattr(reserva, 'motivo', '') or '',
    }

    clinica = _clinica_de_paciente(paciente)

    # Correo al paciente
    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Confirmación de cita — KenkoMed',
            plantilla='emails/reserva_creada.html',
            contexto={**contexto, 'es_paciente': True},
            destinatarios=[paciente.correo],
            clinica=clinica,
        )

    # Correo al clínico
    if clinico and getattr(clinico, 'correo', None):
        _enviar_correo(
            asunto='Nueva reserva agendada — KenkoMed',
            plantilla='emails/reserva_creada.html',
            contexto={**contexto, 'es_paciente': False},
            destinatarios=[clinico.correo],
            clinica=clinica,
        )


def notificar_reserva_reagendada(paciente, clinico, reserva):
    """Notifica al paciente y al clínico cuando su cita es reagendada."""
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else "Su profesional",
        'clinico_profesion': getattr(clinico, 'profesion', '') if clinico else '',
        'fecha': _formatear_fecha(getattr(reserva, 'fecha', None), '%d/%m/%Y'),
        'hora_inicio': _formatear_fecha(getattr(reserva, 'hora_inicio', None), '%H:%M'),
        'hora_fin': _formatear_fecha(getattr(reserva, 'hora_fin', None), '%H:%M'),
    }

    clinica = _clinica_de_paciente(paciente)

    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Cambio de horario de cita — KenkoMed',
            plantilla='emails/reserva_reagendada.html',
            contexto={**contexto, 'es_paciente': True},
            destinatarios=[paciente.correo],
            clinica=clinica,
        )

    if clinico and getattr(clinico, 'correo', None):
        _enviar_correo(
            asunto='Cita reagendada en agenda — KenkoMed',
            plantilla='emails/reserva_reagendada.html',
            contexto={**contexto, 'es_paciente': False},
            destinatarios=[clinico.correo],
            clinica=clinica,
        )


def notificar_reserva_cancelada(paciente, clinico, fecha, hora_inicio):
    """Notifica al paciente y al clínico cuando su cita es cancelada."""
    contexto = {
        'paciente_nombre': getattr(paciente, 'nombre', ''),
        'paciente_apellido': getattr(paciente, 'apellido', ''),
        'clinico_nombre': f"{clinico.nombre} {clinico.apellido}" if clinico else "Su profesional",
        'clinico_profesion': getattr(clinico, 'profesion', '') if clinico else '',
        'fecha': _formatear_fecha(fecha, '%d/%m/%Y'),
        'hora_inicio': _formatear_fecha(hora_inicio, '%H:%M'),
    }

    clinica = _clinica_de_paciente(paciente)

    if paciente and getattr(paciente, 'correo', None):
        _enviar_correo(
            asunto='Cancelación de cita — KenkoMed',
            plantilla='emails/reserva_cancelada.html',
            contexto={**contexto, 'es_paciente': True},
            destinatarios=[paciente.correo],
            clinica=clinica,
        )

    if clinico and getattr(clinico, 'correo', None):
        _enviar_correo(
            asunto='Cita cancelada en agenda — KenkoMed',
            plantilla='emails/reserva_cancelada.html',
            contexto={**contexto, 'es_paciente': False},
            destinatarios=[clinico.correo],
            clinica=clinica,
        )
