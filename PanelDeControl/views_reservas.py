import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from Login.models import Reserva, Paciente, Clinico
from django.core.mail import send_mail
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from django.conf import settings

@requiere_clinico
def calendario_view(request):
    try:
        clinico = Clinico.objects.get(rut=request.session['rut_clinico'])
        # Obtenemos pacientes asignados a este clínico o pacientes de la base general si es admin
        es_admin = request.session.get('es_admin', False)
        if es_admin:
            pacientes = Paciente.objects.all()
        else:
            pacientes = Paciente.objects.filter(clinico=clinico)
    except Exception as e:
        pacientes = []
        
    return render(request, 'calendario.html', {'pacientes': pacientes})

@requiere_clinico
def api_obtener_reservas(request):
    try:
        clinico = Clinico.objects.get(rut=request.session['rut_clinico'])
        # if admin, maybe all? Let's just return to the clinician
        reservas = Reserva.objects.filter(clinico=clinico)
        eventos = []
        for r in reservas:
            eventos.append({
                'id': r.id,
                'title': f"{r.paciente.nombre} {r.paciente.apellido}",
                'start': f"{r.fecha}T{r.hora_inicio.strftime('%H:%M:%S')}",
                'end': f"{r.fecha}T{r.hora_fin.strftime('%H:%M:%S')}",
                'extendedProps': {
                    'paciente_id': r.paciente.rut,
                    'estado': r.estado,
                    'motivo': r.motivo,
                    'correo': r.paciente.correo or ''
                },
                'backgroundColor': '#10b981' if r.estado == 'Confirmada' else '#f59e0b',
                'borderColor': 'transparent',
            })
        return JsonResponse(eventos, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@requiere_clinico
def api_crear_reserva(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            clinico = Clinico.objects.get(rut=request.session['rut_clinico'])
            paciente = get_object_or_404(Paciente, rut=data['paciente_rut'])
            
            # Actualizar el correo si fue enviado
            correo_nuevo = data.get('correo')
            if correo_nuevo:
                paciente.correo = correo_nuevo
                paciente.save()
                
            if not paciente.correo:
                return JsonResponse({'status': 'error', 'message': 'El correo del paciente es obligatorio para agendar la reserva.'}, status=400)
                
            formato_hora = "%H:%M"
            h_inicio = datetime.strptime(data['hora_inicio'][:5], formato_hora).time()
            h_fin = datetime.strptime(data['hora_fin'][:5], formato_hora).time()
            
            if h_inicio >= h_fin:
                return JsonResponse({'status': 'error', 'message': 'La hora de inicio debe ser anterior a la hora de fin.'}, status=400)
                
            hora_apertura = datetime.strptime("07:00", formato_hora).time()
            hora_cierre = datetime.strptime("21:00", formato_hora).time()
            if h_inicio < hora_apertura or h_fin > hora_cierre:
                return JsonResponse({'status': 'error', 'message': 'El horario de atención es de 07:00 a 21:00.'}, status=400)
                
            solapamientos = Reserva.objects.filter(
                clinico=clinico,
                fecha=data['fecha'],
                hora_inicio__lt=data['hora_fin'],
                hora_fin__gt=data['hora_inicio']
            )
            if solapamientos.exists():
                return JsonResponse({'status': 'error', 'message': 'El profesional ya tiene agendada una reserva que cruza en este horario.'}, status=400)
                
            reserva = Reserva.objects.create(
                paciente=paciente,
                clinico=clinico,
                fecha=data['fecha'],
                hora_inicio=data['hora_inicio'],
                hora_fin=data['hora_fin'],
                estado='Confirmada',
                motivo=data.get('motivo', '')
            )
            
            # Enviar correo
            asunto = "Confirmación de Reserva Médica - KenkoMed"
            mensaje = f"""Hola {paciente.nombre},

Tu reserva con el profesional {clinico.nombre} {clinico.apellido} ({clinico.profesion}) ha sido agendada con éxito.

Detalles de la cita:
- Fecha: {reserva.fecha}
- Hora: {reserva.hora_inicio} a {reserva.hora_fin}
- Motivo: {reserva.motivo}

Te esperamos.
Saludos,
KenkoMed
"""
            try:
                send_mail(
                    asunto,
                    mensaje,
                    settings.EMAIL_HOST_USER,
                    [paciente.correo],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error al enviar correo SMTP (revisa tu settings o credenciales de gmail): {e}")
                
            return JsonResponse({'status': 'success', 'id': reserva.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@requiere_clinico
def api_mover_reserva(request, reserva_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            clinico = Clinico.objects.get(rut=request.session['rut_clinico'])
            reserva = get_object_or_404(Reserva, id=reserva_id, clinico=clinico)
            
            formato_hora = "%H:%M"
            h_inicio = datetime.strptime(data['hora_inicio'][:5], formato_hora).time()
            h_fin = datetime.strptime(data['hora_fin'][:5], formato_hora).time()
            
            if h_inicio >= h_fin:
                return JsonResponse({'status': 'error', 'message': 'La hora de inicio debe ser anterior a la hora de fin.'}, status=400)
                
            hora_apertura = datetime.strptime("07:00", formato_hora).time()
            hora_cierre = datetime.strptime("21:00", formato_hora).time()
            if h_inicio < hora_apertura or h_fin > hora_cierre:
                return JsonResponse({'status': 'error', 'message': 'El horario de atención es de 07:00 a 21:00.'}, status=400)
                
            solapamientos = Reserva.objects.filter(
                clinico=clinico,
                fecha=data['fecha'],
                hora_inicio__lt=data['hora_fin'],
                hora_fin__gt=data['hora_inicio']
            ).exclude(id=reserva_id)
            
            if solapamientos.exists():
                return JsonResponse({'status': 'error', 'message': 'El profesional ya tiene agendada una consulta en este horario.'}, status=400)
            
            reserva.fecha = data['fecha']
            reserva.hora_inicio = data['hora_inicio']
            reserva.hora_fin = data['hora_fin']
            reserva.save()
            
            # Enviar correo de reagendamiento
            if reserva.paciente.correo:
                asunto = "Cambio de Horario: Su cita ha sido reagendada - KenkoMed"
                mensaje = f"""Hola {reserva.paciente.nombre},

Tu cita médica con el profesional {clinico.nombre} {clinico.apellido} ({clinico.profesion}) ha sido reagendada a un nuevo horario.

Nuevos detalles de tu cita:
- Fecha: {reserva.fecha}
- Hora: {reserva.hora_inicio} a {reserva.hora_fin}

¡Te esperamos!
Si este cambio es un error, por favor ponte en contacto de inmediato.

Saludos,
KenkoMed
"""
                try:
                    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [reserva.paciente.correo], fail_silently=True)
                except Exception as e:
                    pass
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@requiere_clinico
def api_eliminar_reserva(request, reserva_id):
    if request.method == 'POST' or request.method == 'DELETE':
        try:
            clinico = Clinico.objects.get(rut=request.session['rut_clinico'])
            reserva = get_object_or_404(Reserva, id=reserva_id, clinico=clinico)
            
            paciente = reserva.paciente
            fecha_cita = reserva.fecha
            hora_cita = reserva.hora_inicio
            
            reserva.delete()
            
            # Enviar correo de cancelación
            if paciente.correo:
                asunto = "Cancelación de Cita Médica - KenkoMed"
                mensaje = f"""Hola {paciente.nombre},

Lamentamos informarte que tu cita con el profesional {clinico.nombre} {clinico.apellido} programada para la fecha {fecha_cita} a las {hora_cita} ha sido CANCELADA.

Por favor ponte en contacto si deseas reagendar tu atención, o accede a nuestro portal para solicitar una nueva fecha.

Disculpa los inconvenientes ocasionados.
Saludos,
KenkoMed
"""
                try:
                    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [paciente.correo], fail_silently=True)
                except Exception as e:
                    pass
                    
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
