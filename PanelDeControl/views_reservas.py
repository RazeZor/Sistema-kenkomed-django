import json
import threading
from datetime import datetime

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from Login.auditoria import registrar_auditoria
from Login.models import Clinico, Paciente, Reserva
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from ProyectoMainAPP.email_service import (
    notificar_reserva_creada,
    notificar_reserva_reagendada,
    notificar_reserva_cancelada,
)
from clinicas.utils import (
    clinico_pertenece_a_sesion,
    filtrar_pacientes_por_sesion,
    filtrar_reservas_por_sesion,
    obtener_clinicos_del_centro,
    paciente_pertenece_a_sesion,
)

HORA_APERTURA = datetime.strptime('07:00', '%H:%M').time()
HORA_CIERRE = datetime.strptime('21:00', '%H:%M').time()
COLORES_PROF = ['#0284c7', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0d9488', '#4338ca']


def _notificar_en_background(func, *args, **kwargs):
    """Envía correos en segundo plano para no bloquear la respuesta HTTP."""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()


def puede_editar_calendario_clinica(request):
    """Solo admin del centro activo (no confundir con admin KenkoMed)."""
    return request.session.get('es_admin_clinica', False)


def _contexto_calendario(request, modo):
    rut_sesion = request.session.get('rut_clinico')

    clinicos = list(
        obtener_clinicos_del_centro(request).only('rut', 'nombre', 'apellido', 'profesion')
    )
    pacientes_list = list(
        filtrar_pacientes_por_sesion(request)
        .values('rut', 'nombre', 'apellido', 'correo')
        .order_by('apellido', 'nombre')
    )

    es_centro_compartido = len(clinicos) > 1
    solo_lectura = modo == 'clinica' and not puede_editar_calendario_clinica(request)

    if modo == 'personal':
        titulo = 'Mi Agenda Personal'
        subtitulo = 'Solo tus citas — puedes crear y modificar'
    else:
        titulo = 'Agenda del Centro'
        subtitulo = (
            'Todas las citas del equipo — solo visualización'
            if solo_lectura
            else 'Todas las citas del equipo — administración'
        )

    return {
        'clinicos': clinicos,
        'pacientes_list': pacientes_list,
        'rut_clinico_sesion': rut_sesion,
        'es_centro_compartido': es_centro_compartido,
        'modo_calendario': modo,
        'solo_lectura': solo_lectura,
        'titulo_calendario': titulo,
        'subtitulo_calendario': subtitulo,
        'puede_editar_clinica': puede_editar_calendario_clinica(request),
    }


def _queryset_reservas(request, alcance, start=None, end=None):
    rut_clinico = request.session.get('rut_clinico')

    base = Reserva.objects.select_related('paciente', 'clinico').only(
        'id', 'fecha', 'hora_inicio', 'hora_fin', 'estado', 'motivo',
        'paciente__rut', 'paciente__nombre', 'paciente__apellido', 'paciente__correo',
        'clinico__rut', 'clinico__nombre', 'clinico__apellido',
    )

    if alcance == 'personal':
        if rut_clinico:
            qs = base.filter(clinico_id=rut_clinico)
        else:
            qs = filtrar_reservas_por_sesion(request, base)
    else:
        qs = filtrar_reservas_por_sesion(request, base)

    if start:
        qs = qs.filter(fecha__gte=start)
    if end:
        qs = qs.filter(fecha__lt=end)

    return qs.order_by('fecha', 'hora_inicio')


def _serializar_evento(r, alcance):
    clinico_nombre = f"{r.clinico.nombre} {r.clinico.apellido}"
    titulo = f"{r.paciente.nombre} {r.paciente.apellido}"
    if alcance == 'clinica':
        titulo = f"{titulo} — {r.clinico.nombre}"

    if alcance == 'clinica':
        idx = sum(ord(c) for c in r.clinico.rut) % len(COLORES_PROF)
        bg = COLORES_PROF[idx]
    elif r.estado == 'Confirmada':
        bg = '#10b981'
    elif r.estado == 'Cancelada':
        bg = '#94a3b8'
    else:
        bg = '#f59e0b'

    return {
        'id': r.id,
        'title': titulo,
        'start': f"{r.fecha}T{r.hora_inicio.strftime('%H:%M:%S')}",
        'end': f"{r.fecha}T{r.hora_fin.strftime('%H:%M:%S')}",
        'extendedProps': {
            'paciente_id': r.paciente.rut,
            'clinico_rut': r.clinico.rut,
            'clinico_nombre': clinico_nombre,
            'estado': r.estado,
            'motivo': r.motivo or '',
            'correo': r.paciente.correo or '',
        },
        'backgroundColor': bg,
        'borderColor': 'transparent',
    }


def _serializar_eventos(reservas, alcance):
    return [_serializar_evento(r, alcance) for r in reservas]


def _obtener_reserva_con_permiso(request, reserva_id, alcance, requiere_edicion=False):
    rut_clinico = request.session.get('rut_clinico')

    if alcance == 'personal':
        if rut_clinico:
            reserva = get_object_or_404(Reserva, id=reserva_id, clinico_id=rut_clinico)
        else:
            reserva = get_object_or_404(filtrar_reservas_por_sesion(request), id=reserva_id)
    else:
        reserva = get_object_or_404(filtrar_reservas_por_sesion(request), id=reserva_id)

    if requiere_edicion and alcance == 'clinica' and not puede_editar_calendario_clinica(request):
        return None
    return reserva


def _parse_horas(data):
    h_inicio = datetime.strptime(data['hora_inicio'][:5], '%H:%M').time()
    h_fin = datetime.strptime(data['hora_fin'][:5], '%H:%M').time()
    if h_inicio >= h_fin:
        raise ValueError('La hora de inicio debe ser anterior a la hora de fin.')
    if h_inicio < HORA_APERTURA or h_fin > HORA_CIERRE:
        raise ValueError('El horario de atención es de 07:00 a 21:00.')
    return h_inicio, h_fin


def _validar_solapamiento(clinico, fecha, hora_inicio, hora_fin, excluir_id=None):
    qs = Reserva.objects.filter(
        clinico=clinico,
        fecha=fecha,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    ).exclude(estado='Cancelada')
    if excluir_id:
        qs = qs.exclude(id=excluir_id)
    return qs.exists()


@requiere_clinico
def calendario_personal_view(request):
    return render(request, 'calendario.html', _contexto_calendario(request, 'personal'))


@requiere_clinico
def calendario_clinica_view(request):
    es_admin = request.session.get('es_admin_clinica', False)
    es_compartido = False
    clinica_id = request.session.get('clinica_id')
    if clinica_id:
        from clinicas.models import Clinica, MembresiaClinica
        clinica = Clinica.objects.filter(id=clinica_id, activa=True).only('tipo').first()
        if clinica and clinica.tipo == 'clinica':
            es_compartido = MembresiaClinica.objects.filter(clinica_id=clinica_id, activo=True).count() > 1
    if not es_admin and not es_compartido:
        messages.error(request, 'No tienes acceso a la agenda del centro.')
        return redirect('calendario_personal')
    return render(request, 'calendario.html', _contexto_calendario(request, 'clinica'))


@requiere_clinico
def calendario_view(request):
    return calendario_personal_view(request)


@requiere_clinico
@require_GET
def api_obtener_reservas(request):
    try:
        alcance = request.GET.get('alcance', 'personal')
        if alcance not in ('personal', 'clinica'):
            alcance = 'personal'

        start = request.GET.get('start', '')[:10] or None
        end = request.GET.get('end', '')[:10] or None

        reservas = _queryset_reservas(request, alcance, start=start, end=end)
        response = JsonResponse(_serializar_eventos(reservas, alcance), safe=False)
        response['Cache-Control'] = 'private, max-age=30'
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@requiere_clinico
def api_crear_reserva(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        alcance = data.get('alcance', 'personal')
        rut_sesion = request.session['rut_clinico']
        clinico = Clinico.objects.get(rut=rut_sesion)

        if alcance == 'clinica':
            if not puede_editar_calendario_clinica(request):
                return JsonResponse(
                    {'status': 'error', 'message': 'Solo administradores pueden crear citas en la agenda del centro.'},
                    status=403,
                )
            clinico_rut = data.get('clinico_rut')
            if clinico_rut:
                clinico_asignado = get_object_or_404(Clinico, rut=clinico_rut)
                if not clinico_pertenece_a_sesion(request, clinico_asignado):
                    return JsonResponse({'status': 'error', 'message': 'Profesional no válido para este centro.'}, status=403)
                clinico = clinico_asignado
        else:
            clinico = Clinico.objects.get(rut=rut_sesion)

        paciente = get_object_or_404(Paciente, rut=data['paciente_rut'])
        if not paciente_pertenece_a_sesion(request, paciente):
            return JsonResponse({'status': 'error', 'message': 'No tienes permisos para agendar a este paciente.'}, status=403)

        correo_nuevo = data.get('correo')
        if correo_nuevo and correo_nuevo != (paciente.correo or ''):
            paciente.correo = correo_nuevo
            paciente.save(update_fields=['correo'])

        if not paciente.correo:
            return JsonResponse({'status': 'error', 'message': 'El correo del paciente es obligatorio.'}, status=400)

        _parse_horas(data)

        if _validar_solapamiento(clinico, data['fecha'], data['hora_inicio'], data['hora_fin']):
            return JsonResponse({'status': 'error', 'message': 'El profesional ya tiene una cita en ese horario.'}, status=400)

        reserva = Reserva.objects.create(
            paciente=paciente,
            clinico=clinico,
            fecha=data['fecha'],
            hora_inicio=data['hora_inicio'],
            hora_fin=data['hora_fin'],
            estado='Confirmada',
            motivo=data.get('motivo', ''),
        )
        registrar_auditoria(
            request, 'reserva_crear', paciente,
            detalle=(
                f"Cita {data['fecha']} {data['hora_inicio']}–{data['hora_fin']}"
                f" — profesional {clinico.nombre} {clinico.apellido}"
            ),
        )
        _notificar_en_background(notificar_reserva_creada, paciente, clinico, reserva)

        evento = _serializar_evento(
            Reserva.objects.select_related('paciente', 'clinico').get(pk=reserva.pk),
            alcance,
        )
        return JsonResponse({'status': 'success', 'id': reserva.id, 'event': evento})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@requiere_clinico
def api_mover_reserva(request, reserva_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        alcance = data.get('alcance', 'personal')
        reserva = _obtener_reserva_con_permiso(request, reserva_id, alcance, requiere_edicion=(alcance == 'clinica'))
        if not reserva:
            return JsonResponse({'status': 'error', 'message': 'No tienes permisos para modificar esta cita.'}, status=403)

        clinico = reserva.clinico
        fecha_anterior = reserva.fecha
        hora_anterior = reserva.hora_inicio
        _parse_horas(data)

        if _validar_solapamiento(clinico, data['fecha'], data['hora_inicio'], data['hora_fin'], excluir_id=reserva_id):
            return JsonResponse({'status': 'error', 'message': 'El profesional ya tiene una cita en ese horario.'}, status=400)

        campos_update = ['fecha', 'hora_inicio', 'hora_fin']
        reserva.fecha = data['fecha']
        reserva.hora_inicio = data['hora_inicio']
        reserva.hora_fin = data['hora_fin']

        if 'motivo' in data:
            reserva.motivo = data.get('motivo', '')
            campos_update.append('motivo')

        reserva.save(update_fields=campos_update)

        registrar_auditoria(
            request, 'reserva_modificar', reserva.paciente,
            detalle=(
                f"Reagendó cita #{reserva_id}: {fecha_anterior} {hora_anterior} "
                f"→ {reserva.fecha} {reserva.hora_inicio}"
            ),
        )

        horario_cambio = fecha_anterior != reserva.fecha or hora_anterior != reserva.hora_inicio
        if horario_cambio and reserva.paciente.correo:
            _notificar_en_background(
                notificar_reserva_reagendada, reserva.paciente, clinico, reserva
            )

        evento = _serializar_evento(
            Reserva.objects.select_related('paciente', 'clinico').get(pk=reserva.pk),
            alcance,
        )
        return JsonResponse({'status': 'success', 'event': evento})
    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@requiere_clinico
def api_eliminar_reserva(request, reserva_id):
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = {}
        if request.body:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                data = {}
        alcance = data.get('alcance', request.GET.get('alcance', 'personal'))
        reserva = _obtener_reserva_con_permiso(request, reserva_id, alcance, requiere_edicion=(alcance == 'clinica'))
        if not reserva:
            return JsonResponse({'status': 'error', 'message': 'No tienes permisos para eliminar esta cita.'}, status=403)

        clinico = reserva.clinico
        paciente = reserva.paciente
        fecha_cita = reserva.fecha
        hora_cita = reserva.hora_inicio
        reserva_id_eliminada = reserva.id
        registrar_auditoria(
            request, 'reserva_eliminar', paciente,
            detalle=f"Eliminó cita #{reserva_id_eliminada} — {fecha_cita} {hora_cita}",
        )
        reserva.delete()

        if paciente.correo:
            _notificar_en_background(
                notificar_reserva_cancelada, paciente, clinico, fecha_cita, hora_cita
            )

        return JsonResponse({'status': 'success', 'id': reserva_id_eliminada})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
