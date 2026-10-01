import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Clinico, InvitacionRegistro
from clinicas.models import Clinica, MembresiaClinica
from planes.models import Plan, SuscripcionClinica

logger = logging.getLogger(__name__)

def onboarding_wizard(request, token):
    invitacion = get_object_or_404(InvitacionRegistro, token=token)

    if invitacion.usado:
        messages.error(request, 'Este enlace de invitación ya ha sido utilizado.')
        return redirect('login')

    if invitacion.plan_recomendado:
        planes_disponibles = [invitacion.plan_recomendado]
    else:
        planes_disponibles = Plan.objects.exclude(codigo='legacy_full').order_by('id')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # --- PASO 1: DATOS DEL CLÍNICO ---
                rut = request.POST.get('rut', '').strip()
                nombre = request.POST.get('nombre', '').strip()
                apellido = request.POST.get('apellido', '').strip()
                correo = request.POST.get('correo', '').strip()
                password = request.POST.get('password', '')
                confirm_password = request.POST.get('confirm_password', '')
                profesion = request.POST.get('profesion', 'Kinesiólogo')
                especialidad = request.POST.get('especialidad', '')
                telefono = request.POST.get('telefono', '')

                if Clinico.objects.filter(rut=rut).exists():
                    messages.error(request, 'El RUT ingresado ya está registrado. Por favor, inicia sesión.')
                    return redirect('onboarding_wizard', token=token)

                if correo and Clinico.objects.filter(correo=correo).exists():
                    messages.error(request, 'El correo ingresado ya está registrado.')
                    return redirect('onboarding_wizard', token=token)

                if password != confirm_password:
                    messages.error(request, 'Las contraseñas no coinciden.')
                    return redirect('onboarding_wizard', token=token)

                clinico = Clinico(
                    rut=rut,
                    nombre=nombre,
                    apellido=apellido,
                    correo=correo,
                    profesion=profesion,
                    especialidad=especialidad,
                    telefono=telefono
                )
                clinico.set_password(password)
                clinico.save()

                # --- PASO 2: PLAN ---
                plan_id = request.POST.get('plan_id')
                plan = get_object_or_404(Plan, id=plan_id)

                # --- PASO 3: DATOS DE LA CLÍNICA / CONSULTA ---
                nombre_clinica = request.POST.get('nombre_clinica', f'Consulta {nombre} {apellido}')
                direccion_clinica = request.POST.get('direccion_clinica', '')
                ciudad_clinica = request.POST.get('ciudad_clinica', '')
                telefono_clinica = request.POST.get('telefono_clinica', '')
                correo_clinica = request.POST.get('correo_clinica', '')
                
                rut_empresa = ''
                tipo_clinica = 'individual'
                
                if plan.codigo == 'clinica':
                    rut_empresa = request.POST.get('rut_empresa', '')
                    tipo_clinica = 'clinica'

                clinica = Clinica.objects.create(
                    nombre=nombre_clinica,
                    rut_empresa=rut_empresa,
                    direccion=direccion_clinica,
                    ciudad=ciudad_clinica,
                    telefono=telefono_clinica,
                    correo=correo_clinica,
                    tipo=tipo_clinica,
                    max_clinicos=plan.max_kinesiologos
                )

                # Membresía admin para el creador
                MembresiaClinica.objects.create(
                    clinico=clinico,
                    clinica=clinica,
                    rol='admin'
                )

                # Suscripción
                SuscripcionClinica.objects.create(
                    clinica=clinica,
                    plan=plan,
                    estado=SuscripcionClinica.ESTADO_PRUEBA
                )
                
                # --- PASO 4: SECRETARIA (Si aplica) ---
                if plan.permite_roles_avanzados and request.POST.get('crear_secretaria') == 'on':
                    rut_sec = request.POST.get('rut_secretaria', '').strip()
                    nombre_sec = request.POST.get('nombre_secretaria', '').strip()
                    apellido_sec = request.POST.get('apellido_secretaria', '').strip()
                    correo_sec = request.POST.get('correo_secretaria', '').strip()
                    password_sec = request.POST.get('password_secretaria', '')

                    if rut_sec and not Clinico.objects.filter(rut=rut_sec).exists():
                        secretaria = Clinico(
                            rut=rut_sec,
                            nombre=nombre_sec,
                            apellido=apellido_sec,
                            correo=correo_sec,
                            profesion='Secretaría / Recepción'
                        )
                        secretaria.set_password(password_sec)
                        secretaria.save()
                        
                        MembresiaClinica.objects.create(
                            clinico=secretaria,
                            clinica=clinica,
                            rol='secretaria'
                        )

                # Marcar token como usado
                invitacion.usado = True
                invitacion.save()

                # Autologin
                request.session['rut_clinico'] = clinico.rut
                request.session['nombre_clinico'] = f"{clinico.nombre} {clinico.apellido}"
                request.session['es_admin'] = clinico.EsAdmin
                request.session['clinica_id'] = clinica.id
                request.session['clinica_nombre'] = clinica.nombre
                request.session['es_admin_clinica'] = True

                messages.success(request, '¡Registro completado con éxito! Bienvenido a KenkoMed.')
                return redirect('panel')

        except Exception as e:
            logger.error(f"Error en onboarding: {e}", exc_info=True)
            messages.error(request, 'Ocurrió un error al procesar tu registro. Intenta nuevamente.')
            return redirect('onboarding_wizard', token=token)

    context = {
        'invitacion': invitacion,
        'planes': planes_disponibles
    }
    return render(request, 'Login/onboarding.html', context)
