import logging
from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_lockout_response
from django.contrib import messages
from django.shortcuts import redirect, render
from Login.models import Clinico

logger = logging.getLogger(__name__)


def validarLogin(request):
    try:
        if request.method == 'POST':
            rut = request.POST.get('rut')
            password = request.POST.get('password')
            recordar = request.POST.get('recordar')

            # Verificar si la IP/usuario está bloqueado por demasiados intentos fallidos
            if AxesProxyHandler.is_locked(request, credentials={'username': rut}):
                return get_lockout_response(request, credentials={'username': rut})

            try:
                rut_clean = rut.strip() if rut else ''
                rut_nodots = rut_clean.replace('.', '')
                
                clinico = Clinico.objects.filter(rut=rut_clean).first() or Clinico.objects.filter(rut=rut_nodots).first()
                if not clinico:
                    raise Clinico.DoesNotExist

                logger.info(f"Intento de login para RUT terminado en: ...{rut_clean[-3:] if rut_clean else '?'}")

                if hasattr(clinico, 'check_password') and clinico.check_password(password):
                    # Login exitoso — resetear contador de axes
                    try:
                        AxesProxyHandler.reset_attempts(request=request, username=rut)
                    except Exception:
                        pass

                    # Guardar datos en sesión
                    request.session['rut_clinico'] = clinico.rut
                    request.session['nombre_clinico'] = f"{clinico.nombre} {clinico.apellido}"
                    request.session['es_admin'] = clinico.EsAdmin

                    from clinicas.models import MembresiaClinica
                    from clinicas.signals import crear_clinica_individual

                    membresia = MembresiaClinica.objects.filter(clinico=clinico, activo=True).first()
                    if not membresia:
                        crear_clinica_individual(clinico)
                        membresia = MembresiaClinica.objects.filter(clinico=clinico, activo=True).first()

                    if membresia:
                        request.session['clinica_id'] = membresia.clinica.id
                        request.session['clinica_nombre'] = membresia.clinica.nombre
                        request.session['es_admin_clinica'] = membresia.rol == 'admin'
                        request.session['es_secretaria'] = membresia.rol == 'secretaria'

                    # Control de "recordar"
                    if recordar:
                        request.session.set_expiry(60 * 60 * 24 * 30)
                    else:
                        request.session.set_expiry(0)

                    return redirect('panel')
                else:
                    # Contraseña incorrecta — registrar intento fallido en axes
                    AxesProxyHandler.user_login_failed(request, credentials={'username': rut})
                    messages.error(request, 'La contraseña ingresada es incorrecta.')
            except Clinico.DoesNotExist:
                # RUT no encontrado — también registrar como intento fallido
                AxesProxyHandler.user_login_failed(request, credentials={'username': rut})
                messages.error(request, 'El RUT ingresado no está registrado.')
            except Exception as e:
                logger.error(f"Error inesperado en login: {type(e).__name__}", exc_info=True)
                messages.error(request, 'Error inesperado. Por favor intente nuevamente.')

        return render(request, 'Login.html')

    except Exception as e:
        logger.error(f"Error crítico en validarLogin: {type(e).__name__}", exc_info=True)
        messages.error(request, 'Error inesperado. Por favor intente nuevamente.')
        return render(request, 'Login.html')