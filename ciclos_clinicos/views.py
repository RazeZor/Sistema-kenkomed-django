from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from clinicas.utils import obtener_clinico_de_sesion, obtener_paciente_por_rut
from ciclos_clinicos.models import CicloClinico
from ciclos_clinicos.permissions import ciclo_pertenece_a_sesion
from ciclos_clinicos.selectors import listar_ciclos_paciente
from ciclos_clinicos.services import (
    CicloClinicoError,
    abandonar_ciclo,
    finalizar_ciclo,
    iniciar_nuevo_ciclo,
)


def _paciente_desde_request(request):
    rut = request.POST.get('rut') or request.GET.get('rut')
    return obtener_paciente_por_rut(request, rut)


@requiere_clinico
@require_http_methods(['POST'])
def iniciar_ciclo_view(request):
    paciente = _paciente_desde_request(request)
    if not paciente:
        messages.error(request, 'Paciente no encontrado o sin permisos.')
        return redirect('historialClinico')

    clinico = obtener_clinico_de_sesion(request)
    motivo = request.POST.get('motivo_consulta', '').strip()

    try:
        ciclo = iniciar_nuevo_ciclo(
            paciente,
            paciente.clinica,
            clinico,
            motivo_consulta=motivo,
            request=request,
        )
        request.session['ciclo_activo_id'] = ciclo.id
        messages.success(request, f'Se inició el ciclo clínico #{ciclo.numero_ciclo}.')
    except CicloClinicoError as exc:
        messages.error(request, str(exc))

    return redirect(f'/panel/historialClinico/?rut={paciente.rut}' + (
        f'&ciclo_id={request.session["ciclo_activo_id"]}' if request.session.get('ciclo_activo_id') else ''
    ))


@requiere_clinico
@require_http_methods(['POST'])
def finalizar_ciclo_view(request):
    paciente = _paciente_desde_request(request)
    ciclo_id = request.POST.get('ciclo_id')
    if not paciente or not ciclo_id:
        messages.error(request, 'Datos incompletos.')
        return redirect('historialClinico')

    try:
        ciclo = CicloClinico.objects.get(pk=ciclo_id, paciente=paciente)
    except CicloClinico.DoesNotExist:
        messages.error(request, 'Ciclo no encontrado.')
        return redirect(f'/panel/historialClinico/?rut={paciente.rut}')

    if not ciclo_pertenece_a_sesion(request, ciclo):
        messages.error(request, 'No tienes permisos sobre este ciclo.')
        return redirect('historialClinico')

    clinico = obtener_clinico_de_sesion(request)
    notas = request.POST.get('notas_cierre', '').strip()

    try:
        finalizar_ciclo(ciclo, clinico=clinico, notas_cierre=notas, request=request)
        if request.session.get('ciclo_activo_id') == ciclo.id:
            request.session.pop('ciclo_activo_id', None)
        messages.success(request, f'Ciclo #{ciclo.numero_ciclo} finalizado.')
    except CicloClinicoError as exc:
        messages.error(request, str(exc))

    return redirect(f'/panel/historialClinico/?rut={paciente.rut}')


@requiere_clinico
@require_http_methods(['POST'])
def abandonar_ciclo_view(request):
    paciente = _paciente_desde_request(request)
    ciclo_id = request.POST.get('ciclo_id')
    if not paciente or not ciclo_id:
        messages.error(request, 'Datos incompletos.')
        return redirect('historialClinico')

    try:
        ciclo = CicloClinico.objects.get(pk=ciclo_id, paciente=paciente)
    except CicloClinico.DoesNotExist:
        messages.error(request, 'Ciclo no encontrado.')
        return redirect(f'/panel/historialClinico/?rut={paciente.rut}')

    if not ciclo_pertenece_a_sesion(request, ciclo):
        messages.error(request, 'No tienes permisos sobre este ciclo.')
        return redirect('historialClinico')

    clinico = obtener_clinico_de_sesion(request)
    motivo = request.POST.get('motivo', '').strip()

    try:
        abandonar_ciclo(ciclo, clinico=clinico, motivo=motivo, request=request)
        if request.session.get('ciclo_activo_id') == ciclo.id:
            request.session.pop('ciclo_activo_id', None)
        messages.warning(request, f'Ciclo #{ciclo.numero_ciclo} marcado como abandonado.')
    except CicloClinicoError as exc:
        messages.error(request, str(exc))

    return redirect(f'/panel/historialClinico/?rut={paciente.rut}')


@requiere_clinico
def listar_ciclos_view(request):
    paciente = _paciente_desde_request(request)
    if not paciente:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)

    clinica_id = request.session.get('clinica_id')
    ciclos = listar_ciclos_paciente(paciente, clinica_id=clinica_id)
    data = [
        {
            'id': c.id,
            'numero_ciclo': c.numero_ciclo,
            'estado': c.estado,
            'estado_display': c.get_estado_display(),
            'fecha_inicio': c.fecha_inicio.isoformat(),
            'fecha_cierre': c.fecha_cierre.isoformat() if c.fecha_cierre else None,
            'motivo_consulta': c.motivo_consulta,
        }
        for c in ciclos
    ]
    return JsonResponse({'ciclos': data})


@requiere_clinico
@require_http_methods(['POST'])
def subir_adjunto_view(request):
    ciclo_id = request.POST.get('ciclo_id')
    archivo = request.FILES.get('archivo')
    
    if not ciclo_id or not archivo:
        return JsonResponse({'error': 'Datos incompletos.'}, status=400)
        
    try:
        ciclo = CicloClinico.objects.get(pk=ciclo_id)
        # Verificar permisos
        if not ciclo_pertenece_a_sesion(request, ciclo):
            return JsonResponse({'error': 'No tienes permisos sobre este ciclo.'}, status=403)
            
        from ciclos_clinicos.models import AdjuntoHistorialClinico
        
        # Validar tamaño (ej. max 10MB)
        if archivo.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'El archivo supera el tamaño máximo de 10 MB.'}, status=400)
            
        adjunto = AdjuntoHistorialClinico(
            ciclo=ciclo,
            archivo=archivo,
            nombre_original=archivo.name,
            peso_bytes=archivo.size
        )
        adjunto.full_clean() # Valida extensión y límite de archivos (regaloneo)
        adjunto.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Archivo subido correctamente.',
            'adjunto': {
                'id': adjunto.id,
                'nombre': adjunto.nombre_original,
                'url': adjunto.archivo.url,
                'fecha': adjunto.fecha_subida.strftime('%d/%m/%Y')
            }
        })
        
    except CicloClinico.DoesNotExist:
        return JsonResponse({'error': 'Ciclo no encontrado.'}, status=404)
    except Exception as e:
        # Podría ser ValidationError
        if hasattr(e, 'message_dict'):
            return JsonResponse({'error': str(e.message_dict)}, status=400)
        elif hasattr(e, 'messages'):
            return JsonResponse({'error': e.messages[0]}, status=400)
        return JsonResponse({'error': str(e)}, status=400)


@requiere_clinico
@require_http_methods(['POST'])
def eliminar_adjunto_view(request):
    adjunto_id = request.POST.get('adjunto_id')
    if not adjunto_id:
        return JsonResponse({'error': 'ID no proporcionado.'}, status=400)
        
    from ciclos_clinicos.models import AdjuntoHistorialClinico
    try:
        adjunto = AdjuntoHistorialClinico.objects.get(pk=adjunto_id)
        if not ciclo_pertenece_a_sesion(request, adjunto.ciclo):
            return JsonResponse({'error': 'No tienes permisos para eliminar este archivo.'}, status=403)
            
        adjunto.archivo.delete(save=False) # Borra archivo del disco/S3
        adjunto.delete()
        
        return JsonResponse({'success': True, 'mensaje': 'Archivo eliminado.'})
    except AdjuntoHistorialClinico.DoesNotExist:
        return JsonResponse({'error': 'Archivo no encontrado.'}, status=404)
