"""
Backend personalizado de correo para Django utilizando la API HTTPS de Resend.
Permite que cualquier llamada a send_mail, EmailMessage o EmailMultiAlternatives
en Django utilice la API de Resend sin depender de puertos SMTP salientes.
"""
import json
import logging
import urllib.request
import urllib.error

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, api_key=None, from_email=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = api_key or getattr(settings, 'RESEND_API_KEY', '')
        self.from_email = from_email or getattr(settings, 'RESEND_FROM_EMAIL', 'KenkoMed <onboarding@resend.dev>')

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        num_sent = 0
        for message in email_messages:
            sent = self._send_one_message(message)
            if sent:
                num_sent += 1
        return num_sent

    def _send_one_message(self, message):
        try:
            recipients = list(message.to)
            if not recipients:
                return False

            resend_from = getattr(settings, 'RESEND_FROM_EMAIL', 'KenkoMed <onboarding@resend.dev>')
            from_email = message.from_email or resend_from
            if 'resend.dev' in resend_from and 'resend.dev' not in str(from_email):
                from_email = resend_from

            body_html = None
            if hasattr(message, 'alternatives'):
                for content, mimetype in message.alternatives:
                    if mimetype == 'text/html':
                        body_html = content
                        break

            if not body_html:
                body_html = f"<pre style='font-family:sans-serif;'>{message.body}</pre>"

            payload = {
                'from': from_email,
                'to': recipients,
                'subject': message.subject,
                'html': body_html,
            }

            reply_to_list = list(message.reply_to) if message.reply_to else ['kenkomedplus@gmail.com']
            if reply_to_list:
                payload['reply_to'] = reply_to_list


            req = urllib.request.Request(
                'https://api.resend.com/emails',
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Resend/Python-SDK',
                }
            )

            response = urllib.request.urlopen(req, timeout=10)
            res_data = json.loads(response.read().decode('utf-8'))
            logger.info(f"Correo enviado por ResendEmailBackend: '{message.subject}' → {recipients} (ID: {res_data.get('id')})")
            return True

        except urllib.error.HTTPError as e:
            body_err = e.read().decode('utf-8', errors='ignore')
            logger.error(f"Error HTTP en ResendEmailBackend ({e.code}): {body_err}")
            if not self.fail_silently:
                raise
            return False
        except Exception as e:
            logger.error(f"Error en ResendEmailBackend enviando '{message.subject}': {e}", exc_info=True)
            if not self.fail_silently:
                raise
            return False
