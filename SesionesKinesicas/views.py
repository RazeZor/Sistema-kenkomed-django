from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from Login.models import Paciente, Clinico
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from .models import SesionKinesica
import json
from datetime import datetime


@requiere_clinico
def listar_sesiones_paciente(request):
    """
    Lista todas las sesiones kinésicas de un paciente.
    Permite seleccionar una sesión para verla o crear una nueva.
    """
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    rut_paciente = request.GET.get('rut') or request.POST.get('rut')
    nombre_clinico = request.session['nombre_clinico']
    rut_clinico = request.session.get('rut_clinico')
    es_admin = request.session.get('es_admin', False)
    
    # Obtener el clínico
    clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
    
    # Obtener el paciente
    try:
        if es_admin:
            paciente = Paciente.objects.get(rut=rut_paciente)
        else:
            if not clinico_obj:
                messages.error(request, 'Error: Clínico no encontrado en sesión.')
                return redirect('historialClinico')
            paciente = Paciente.objects.get(rut=rut_paciente, clinico=clinico_obj)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('historialClinico')
    
    # Obtener todas las sesiones del paciente
    sesiones = SesionKinesica.objects.filter(paciente=paciente).order_by('-numero_sesion')
    primera_sesion = sesiones.filter(es_primera_sesion=True).first()
    sesiones_posteriores = sesiones.filter(es_primera_sesion=False)
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'primera_sesion': primera_sesion,
        'sesiones_posteriores': sesiones_posteriores,
        'hay_sesiones': sesiones.exists(),
        'total_sesiones': sesiones.count(),
    }
    
    return render(request, 'SesionesKinesicas/listar_sesiones.html', context)


@requiere_clinico
def crear_primera_sesion(request):
    """
    Crea la primera sesión kinésica de un paciente con formulario detallado.
    """
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    rut_paciente = request.GET.get('rut') or request.POST.get('rut')
    nombre_clinico = request.session['nombre_clinico']
    rut_clinico = request.session.get('rut_clinico')
    es_admin = request.session.get('es_admin', False)
    
    # Obtener el clínico
    clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
    
    # Obtener el paciente
    try:
        if es_admin:
            paciente = Paciente.objects.get(rut=rut_paciente)
        else:
            if not clinico_obj:
                messages.error(request, 'Error: Clínico no encontrado en sesión.')
                return redirect('historialClinico')
            paciente = Paciente.objects.get(rut=rut_paciente, clinico=clinico_obj)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Verificar que no exista una primera sesión
    if SesionKinesica.objects.filter(paciente=paciente, es_primera_sesion=True).exists():
        messages.warning(request, 'Este paciente ya tiene una sesión inicial. Crea una sesión de seguimiento.')
        return redirect('listar_sesiones_kinesicas', rut=rut_paciente)
    
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            evaluacion_datos = {
                # ANAMNESIS
                'motivo_consulta': request.POST.get('motivo_consulta', ''),
                'causa_lesion': request.POST.get('causa_lesion', ''),
                'mecanismo_lesion': request.POST.get('mecanismo_lesion', ''),
                'manejo_abordaje': request.POST.get('manejo_abordaje', ''),
                'fecha_lesion': request.POST.get('fecha_lesion', ''),
                'fecha_control_medico': request.POST.get('fecha_control_medico', ''),
                'alteraciones_funcionales': request.POST.get('alteraciones_funcionales', ''),
                'objetivo_paciente': request.POST.get('objetivo_paciente', ''),
                
                # EVALUACIÓN DEL DOLOR
                'dolor_presente': request.POST.get('dolor_presente', ''),
                'dolor_antiguedad': request.POST.get('dolor_antiguedad', ''),
                'dolor_localizacion': request.POST.get('dolor_localizacion', ''),
                'dolor_intensidad': request.POST.get('dolor_intensidad', ''),
                'dolor_caracteristicas': request.POST.get('dolor_caracteristicas', ''),
                'dolor_irradiacion': request.POST.get('dolor_irradiacion', ''),
                
                # EVALUACIÓN POSTURAL
                'postura_plano_frontal_anterior': request.POST.get('postura_plano_frontal_anterior', ''),
                'postura_plano_frontal_posterior': request.POST.get('postura_plano_frontal_posterior', ''),
                'postura_plano_sagital': request.POST.get('postura_plano_sagital', ''),
                
                # EXAMEN FÍSICO
                'examen_observacion': request.POST.get('examen_observacion', ''),
                'examen_inspeccion': request.POST.get('examen_inspeccion', ''),
                'examen_palpacion': request.POST.get('examen_palpacion', ''),
                
                # RANGO ARTICULAR ACTIVO
                'rango_activo_conservados': request.POST.get('rango_activo_conservados', ''),
                'rango_activo_limitados': request.POST.get('rango_activo_limitados', ''),
                
                # RANGO ARTICULAR PASIVO
                'rango_pasivo_mmss_derecha': request.POST.get('rango_pasivo_mmss_derecha', ''),
                'rango_pasivo_mmss_izquierda': request.POST.get('rango_pasivo_mmss_izquierda', ''),
                'rango_pasivo_mmii_derecha': request.POST.get('rango_pasivo_mmii_derecha', ''),
                'rango_pasivo_mmii_izquierda': request.POST.get('rango_pasivo_mmii_izquierda', ''),
                
                # FUNCIÓN MUSCULAR
                'funcion_muscular_superiores': request.POST.get('funcion_muscular_superiores', ''),
                'funcion_muscular_inferiores': request.POST.get('funcion_muscular_inferiores', ''),
                
                # PRUEBAS FUNCIONALES ACTIVAS
                'movimiento_squat_overhead': request.POST.get('movimiento_squat_overhead', ''),
                'movimiento_single_leg_squat': request.POST.get('movimiento_single_leg_squat', ''),
                'movimiento_drop_test': request.POST.get('movimiento_drop_test', ''),
                'movimiento_salto_cajon': request.POST.get('movimiento_salto_cajon', ''),
                
                # EVALUACIÓN DE MOVIMIENTO CON CARGA
                'movimiento_carga_squat_press': request.POST.get('movimiento_carga_squat_press', ''),
                'movimiento_carga_split_deadlift': request.POST.get('movimiento_carga_split_deadlift', ''),
                'movimiento_carga_turkish_get_up': request.POST.get('movimiento_carga_turkish_get_up', ''),
                
                # TEST ORTOPÉDICOS
                'test_ortopedicos': request.POST.get('test_ortopedicos', ''),
            }
            
            notas = request.POST.get('notas_clinicas', '')
            evolucion = request.POST.get('evolucion', '')
            
            # Crear la sesión
            sesion = SesionKinesica.objects.create(
                paciente=paciente,
                clinico=clinico_obj if not es_admin else Clinico.objects.first(),  # Fallback para admin
                numero_sesion=1,
                es_primera_sesion=True,
                evaluacion_inicial=evaluacion_datos,
                notas_clinicas=notas,
                evolucion=evolucion,
            )
            
            messages.success(request, 'Primera sesión kinésica creada exitosamente.')
            return redirect('sesiones_kinesicas:ver') + f'?rut={rut_paciente}&numero_sesion=1'
            
        except Exception as e:
            messages.error(request, f'Error al crear la sesión: {str(e)}')
            return render(request, 'SesionesKinesicas/crear_primera_sesion.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
            })
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'rut': rut_paciente,
    }
    
    return render(request, 'SesionesKinesicas/crear_primera_sesion.html', context)


@requiere_clinico
def crear_sesion_seguimiento(request):
    """
    Crea una sesión de seguimiento (sesión posterior a la primera).
    Solo contiene notas clínicas y evolución en texto libre.
    """
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    rut_paciente = request.GET.get('rut') or request.POST.get('rut')
    nombre_clinico = request.session['nombre_clinico']
    rut_clinico = request.session.get('rut_clinico')
    es_admin = request.session.get('es_admin', False)
    
    # Obtener el clínico
    clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
    
    # Obtener el paciente
    try:
        if es_admin:
            paciente = Paciente.objects.get(rut=rut_paciente)
        else:
            if not clinico_obj:
                messages.error(request, 'Error: Clínico no encontrado en sesión.')
                return redirect('historialClinico')
            paciente = Paciente.objects.get(rut=rut_paciente, clinico=clinico_obj)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Verificar que exista una primera sesión
    if not SesionKinesica.objects.filter(paciente=paciente, es_primera_sesion=True).exists():
        messages.error(request, 'Primero debes crear una sesión inicial.')
        return redirect('crear_primera_sesion_kinesica', rut=rut_paciente)
    
    if request.method == 'POST':
        try:
            # Obtener el siguiene número de sesión
            ultima_sesion = SesionKinesica.objects.filter(
                paciente=paciente
            ).order_by('-numero_sesion').first()
            nuevo_numero = (ultima_sesion.numero_sesion if ultima_sesion else 0) + 1
            
            notas = request.POST.get('notas_clinicas', '')
            evolucion = request.POST.get('evolucion', '')
            
            # Crear la sesión de seguimiento
            sesion = SesionKinesica.objects.create(
                paciente=paciente,
                clinico=clinico_obj if not es_admin else Clinico.objects.first(),
                numero_sesion=nuevo_numero,
                es_primera_sesion=False,
                notas_clinicas=notas,
                evolucion=evolucion,
            )
            
            messages.success(request, f'Sesión #{nuevo_numero} creada exitosamente.')
            return redirect('sesiones_kinesicas:ver') + f'?rut={rut_paciente}&numero_sesion={nuevo_numero}'
            
        except Exception as e:
            messages.error(request, f'Error al crear la sesión: {str(e)}')
    
    # Obtener la última sesión para mostrar información
    ultima_sesion = SesionKinesica.objects.filter(
        paciente=paciente
    ).order_by('-numero_sesion').first()
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'rut': rut_paciente,
        'ultima_sesion': ultima_sesion,
        'proximo_numero': (ultima_sesion.numero_sesion + 1) if ultima_sesion else 2,
    }
    
    return render(request, 'SesionesKinesicas/crear_sesion_seguimiento.html', context)


@requiere_clinico
def ver_sesion_kinesica(request):
    """
    Visualiza una sesión kinésica específica.
    """
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    rut_paciente = request.GET.get('rut')
    numero_sesion = request.GET.get('numero_sesion')
    nombre_clinico = request.session['nombre_clinico']
    rut_clinico = request.session.get('rut_clinico')
    es_admin = request.session.get('es_admin', False)
    
    # Obtener el clínico
    clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
    
    # Obtener el paciente
    try:
        if es_admin:
            paciente = Paciente.objects.get(rut=rut_paciente)
        else:
            if not clinico_obj:
                messages.error(request, 'Error: Clínico no encontrado en sesión.')
                return redirect('historialClinico')
            paciente = Paciente.objects.get(rut=rut_paciente, clinico=clinico_obj)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Obtener la sesión
    sesion = get_object_or_404(
        SesionKinesica,
        paciente=paciente,
        numero_sesion=numero_sesion
    )
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'sesion': sesion,
        'es_primera_sesion': sesion.es_primera_sesion,
    }
    
    return render(request, 'SesionesKinesicas/ver_sesion.html', context)


@requiere_clinico
def editar_sesion_kinesica(request):
    """
    Edita una sesión kinésica existente.
    """
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    rut_paciente = request.GET.get('rut') or request.POST.get('rut')
    numero_sesion = request.GET.get('numero_sesion') or request.POST.get('numero_sesion')
    nombre_clinico = request.session['nombre_clinico']
    rut_clinico = request.session.get('rut_clinico')
    es_admin = request.session.get('es_admin', False)
    
    # Obtener el clínico
    clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
    
    # Obtener el paciente
    try:
        if es_admin:
            paciente = Paciente.objects.get(rut=rut_paciente)
        else:
            if not clinico_obj:
                messages.error(request, 'Error: Clínico no encontrado en sesión.')
                return redirect('historialClinico')
            paciente = Paciente.objects.get(rut=rut_paciente, clinico=clinico_obj)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Obtener la sesión
    sesion = get_object_or_404(
        SesionKinesica,
        paciente=paciente,
        numero_sesion=numero_sesion
    )
    
    if request.method == 'POST':
        try:
            # Actualizar notas y evolución (campos comunes a todas las sesiones)
            sesion.notas_clinicas = request.POST.get('notas_clinicas', '')
            sesion.evolucion = request.POST.get('evolucion', '')
            
            # Si es la primera sesión, actualizar también la evaluación inicial
            if sesion.es_primera_sesion:
                evaluacion_datos = {
                    # ANAMNESIS
                    'motivo_consulta': request.POST.get('motivo_consulta', ''),
                    'causa_lesion': request.POST.get('causa_lesion', ''),
                    'mecanismo_lesion': request.POST.get('mecanismo_lesion', ''),
                    'manejo_abordaje': request.POST.get('manejo_abordaje', ''),
                    'fecha_lesion': request.POST.get('fecha_lesion', ''),
                    'fecha_control_medico': request.POST.get('fecha_control_medico', ''),
                    'alteraciones_funcionales': request.POST.get('alteraciones_funcionales', ''),
                    'objetivo_paciente': request.POST.get('objetivo_paciente', ''),
                    
                    # EVALUACIÓN DEL DOLOR
                    'dolor_presente': request.POST.get('dolor_presente', ''),
                    'dolor_antiguedad': request.POST.get('dolor_antiguedad', ''),
                    'dolor_localizacion': request.POST.get('dolor_localizacion', ''),
                    'dolor_intensidad': request.POST.get('dolor_intensidad', ''),
                    'dolor_caracteristicas': request.POST.get('dolor_caracteristicas', ''),
                    'dolor_irradiacion': request.POST.get('dolor_irradiacion', ''),
                    
                    # EVALUACIÓN POSTURAL
                    'postura_plano_frontal_anterior': request.POST.get('postura_plano_frontal_anterior', ''),
                    'postura_plano_frontal_posterior': request.POST.get('postura_plano_frontal_posterior', ''),
                    'postura_plano_sagital': request.POST.get('postura_plano_sagital', ''),
                    
                    # EXAMEN FÍSICO
                    'examen_observacion': request.POST.get('examen_observacion', ''),
                    'examen_inspeccion': request.POST.get('examen_inspeccion', ''),
                    'examen_palpacion': request.POST.get('examen_palpacion', ''),
                    
                    # RANGO ARTICULAR ACTIVO
                    'rango_activo_conservados': request.POST.get('rango_activo_conservados', ''),
                    'rango_activo_limitados': request.POST.get('rango_activo_limitados', ''),
                    
                    # RANGO ARTICULAR PASIVO
                    'rango_pasivo_mmss_derecha': request.POST.get('rango_pasivo_mmss_derecha', ''),
                    'rango_pasivo_mmss_izquierda': request.POST.get('rango_pasivo_mmss_izquierda', ''),
                    'rango_pasivo_mmii_derecha': request.POST.get('rango_pasivo_mmii_derecha', ''),
                    'rango_pasivo_mmii_izquierda': request.POST.get('rango_pasivo_mmii_izquierda', ''),
                    
                    # FUNCIÓN MUSCULAR
                    'funcion_muscular_superiores': request.POST.get('funcion_muscular_superiores', ''),
                    'funcion_muscular_inferiores': request.POST.get('funcion_muscular_inferiores', ''),
                    
                    # PRUEBAS FUNCIONALES ACTIVAS
                    'movimiento_squat_overhead': request.POST.get('movimiento_squat_overhead', ''),
                    'movimiento_single_leg_squat': request.POST.get('movimiento_single_leg_squat', ''),
                    'movimiento_drop_test': request.POST.get('movimiento_drop_test', ''),
                    'movimiento_salto_cajon': request.POST.get('movimiento_salto_cajon', ''),
                    
                    # EVALUACIÓN DE MOVIMIENTO CON CARGA
                    'movimiento_carga_squat_press': request.POST.get('movimiento_carga_squat_press', ''),
                    'movimiento_carga_split_deadlift': request.POST.get('movimiento_carga_split_deadlift', ''),
                    'movimiento_carga_turkish_get_up': request.POST.get('movimiento_carga_turkish_get_up', ''),
                    
                    # TEST ORTOPÉDICOS
                    'test_ortopedicos': request.POST.get('test_ortopedicos', ''),
                }
                sesion.evaluacion_inicial = evaluacion_datos
            
            sesion.save()
            messages.success(request, 'Sesión actualizada exitosamente.')
            return redirect('sesiones_kinesicas:ver') + f'?rut={rut_paciente}&numero_sesion={numero_sesion}'
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la sesión: {str(e)}')
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'sesion': sesion,
        'es_primera_sesion': sesion.es_primera_sesion,
        'rut': rut_paciente,
    }
    
    return render(request, 'SesionesKinesicas/editar_sesion.html', context)


@csrf_exempt
def api_sesiones_paciente(request):
    """
    API para obtener las sesiones de un paciente (usado por el combobox).
    """
    if 'nombre_clinico' not in request.session:
        return JsonResponse({'error': 'No autorizado'}, status=401)
    
    rut_paciente = request.GET.get('rut')
    
    if not rut_paciente:
        return JsonResponse({'error': 'RUT no proporcionado'}, status=400)
    
    try:
        paciente = Paciente.objects.get(rut=rut_paciente)
        sesiones = SesionKinesica.objects.filter(paciente=paciente).order_by('-numero_sesion')
        
        sesiones_data = [
            {
                'numero_sesion': s.numero_sesion,
                'fecha': s.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'es_primera': s.es_primera_sesion,
                'tipo': 'Evaluación Inicial' if s.es_primera_sesion else f'Sesión #{s.numero_sesion}',
            }
            for s in sesiones
        ]
        
        return JsonResponse({
            'paciente': f'{paciente.nombre} {paciente.apellido}',
            'sesiones': sesiones_data,
            'total': sesiones.count(),
        })
        
    except Paciente.DoesNotExist:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
