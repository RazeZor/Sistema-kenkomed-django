"""
Comando de diagnóstico para probar la conectividad SMTP desde el servidor.
Uso: python manage.py test_email destino@email.com
"""
import socket
import smtplib
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail


class Command(BaseCommand):
    help = 'Diagnostica y prueba el envío de correos SMTP paso a paso'

    def add_arguments(self, parser):
        parser.add_argument('email', nargs='?', default='kenkomedplus@gmail.com',
                            help='Dirección de correo destino para la prueba')

    def handle(self, *args, **options):
        dest = options['email']
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('  DIAGNÓSTICO DE CORREO SMTP — KenkoMed')
        self.stdout.write('=' * 60)

        # 1. Mostrar configuración actual
        self.stdout.write(f'\n[CONFIG]')
        self.stdout.write(f'  EMAIL_BACKEND:      {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  EMAIL_HOST:          {settings.EMAIL_HOST}')
        self.stdout.write(f'  EMAIL_PORT:          {settings.EMAIL_PORT}')
        self.stdout.write(f'  EMAIL_USE_TLS:       {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'  EMAIL_USE_SSL:       {getattr(settings, "EMAIL_USE_SSL", False)}')
        self.stdout.write(f'  EMAIL_TIMEOUT:       {getattr(settings, "EMAIL_TIMEOUT", None)}')
        self.stdout.write(f'  EMAIL_HOST_USER:     {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'  EMAIL_HOST_PASSWORD: {"***" + settings.EMAIL_HOST_PASSWORD[-4:] if settings.EMAIL_HOST_PASSWORD else "(vacío)"}')
        self.stdout.write(f'  DEFAULT_FROM_EMAIL:  {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'  EMAIL_BCC_SYSTEM:    {getattr(settings, "EMAIL_BCC_SYSTEM", "(no definido)")}')

        # 2. Resolver DNS
        self.stdout.write(f'\n[DNS] Resolviendo {settings.EMAIL_HOST}...')
        try:
            ip = socket.gethostbyname(settings.EMAIL_HOST)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Resuelto: {ip}'))
        except socket.gaierror as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error DNS: {e}'))
            return

        # 3. Probar conexión TCP al puerto 587
        self.stdout.write(f'\n[TCP] Conectando a {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...')
        try:
            t0 = time.time()
            sock = socket.create_connection(
                (settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=10
            )
            sock.close()
            self.stdout.write(self.style.SUCCESS(f'  ✓ Puerto {settings.EMAIL_PORT} ABIERTO ({time.time()-t0:.2f}s)'))
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Puerto {settings.EMAIL_PORT} BLOQUEADO: {e}'))
            self.stdout.write(self.style.WARNING(
                '\n  >>> El puerto 587 está bloqueado por tu proveedor de hosting.\n'
                '  >>> Prueba cambiar a puerto 465 con SSL:\n'
                '  >>>   EMAIL_PORT=465\n'
                '  >>>   EMAIL_USE_TLS=False\n'
                '  >>>   EMAIL_USE_SSL=True\n'
            ))

            # Probar puerto 465 automáticamente
            self.stdout.write(f'\n[TCP] Probando puerto alternativo 465...')
            try:
                t0 = time.time()
                sock = socket.create_connection(
                    (settings.EMAIL_HOST, 465), timeout=10
                )
                sock.close()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Puerto 465 ABIERTO ({time.time()-t0:.2f}s)'))
                self.stdout.write(self.style.WARNING(
                    '\n  >>> ¡Puerto 465 funciona! Cambia tu configuración a:\n'
                    '  >>>   EMAIL_PORT=465, EMAIL_USE_TLS=False, EMAIL_USE_SSL=True\n'
                ))
            except Exception as e2:
                self.stdout.write(self.style.ERROR(f'  ✗ Puerto 465 también bloqueado: {e2}'))
                self.stdout.write(self.style.ERROR(
                    '\n  >>> Ambos puertos están bloqueados. Contacta a tu proveedor\n'
                    '  >>> de hosting para desbloquear el tráfico SMTP saliente.\n'
                ))
            return

        # 4. Probar handshake SMTP
        self.stdout.write(f'\n[SMTP] Realizando handshake SMTP...')
        try:
            t0 = time.time()
            if getattr(settings, 'EMAIL_USE_SSL', False):
                smtp = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            else:
                smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
                if settings.EMAIL_USE_TLS:
                    smtp.starttls()
            self.stdout.write(self.style.SUCCESS(f'  ✓ TLS/SSL establecido ({time.time()-t0:.2f}s)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Handshake falló: {e}'))
            return

        # 5. Probar login
        self.stdout.write(f'\n[AUTH] Autenticando como {settings.EMAIL_HOST_USER}...')
        try:
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Login exitoso'))
            smtp.quit()
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error de autenticación: {e}'))
            self.stdout.write(self.style.WARNING(
                '  >>> Verifica que EMAIL_HOST_PASSWORD sea un App Password válido de Gmail.\n'
            ))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {e}'))
            return

        # 6. Enviar correo real con Django
        self.stdout.write(f'\n[ENVÍO] Enviando correo de prueba a {dest}...')
        try:
            t0 = time.time()
            result = send_mail(
                subject='✓ Prueba SMTP KenkoMed — Producción',
                message='Este correo confirma que el envío SMTP desde producción funciona correctamente.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[dest],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Correo enviado exitosamente ({time.time()-t0:.2f}s) — Resultado: {result}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error al enviar: {e}'))

        self.stdout.write('\n' + '=' * 60 + '\n')
