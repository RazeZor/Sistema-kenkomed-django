from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from Login.models import Paciente, Clinico
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from ProyectoMainAPP.email_service import notificar_alta_paciente
from Login.auditoria import registrar_auditoria
from clinicas.utils import obtener_paciente_por_rut
from .session_inputs import evaluacion_inicial_desde_post, validar_post_sesion_kinesica
from .models import SesionKinesica, RegistroEscalaSesion
from .escalas_sesion import obtener_escalas_agrupadas_por_numero, paquetes_escalas_para_paciente
from TiposDeFormularios.escalas_graficos import graficos_para_registros_sesion
import json
from datetime import datetime


def obtener_paciente_con_permiso(rut_paciente, request):
    return obtener_paciente_por_rut(request, rut_paciente)


def _rechazar_texto_marcado(request, post, *, incluir_evaluacion=False, incluir_final=False):
    """Muestra errores y retorna True si hay HTML/CSS/JS en campos de texto."""
    errores = validar_post_sesion_kinesica(
        post,
        incluir_evaluacion=incluir_evaluacion,
        incluir_final=incluir_final,
    )
    if not errores:
        return False
    for err in errores:
        messages.error(request, err)
    messages.error(
        request,
        'No se guardó la sesión. Los campos clínicos deben ser texto plano, sin HTML, CSS ni JavaScript.',
    )
    return True

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
    
    # Obtener el paciente
    try:
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('historialClinico')
    
    # Obtener todas las sesiones del paciente
    sesiones = SesionKinesica.objects.filter(paciente=paciente).order_by('-numero_sesion')
    primera_sesion = sesiones.filter(es_primera_sesion=True).first()
    sesiones_posteriores = list(sesiones.filter(es_primera_sesion=False))
    escalas_por_numero = obtener_escalas_agrupadas_por_numero(paciente)
    if primera_sesion:
        primera_sesion.escalas_en_sesion = escalas_por_numero.get(primera_sesion.numero_sesion, [])
    for s in sesiones_posteriores:
        s.escalas_en_sesion = escalas_por_numero.get(s.numero_sesion, [])
        s.graficos_escalas = graficos_para_registros_sesion(paciente, s.escalas_en_sesion)
        s.graficos_escalas_json = json.dumps(s.graficos_escalas, ensure_ascii=False)
    if primera_sesion:
        primera_sesion.graficos_escalas = graficos_para_registros_sesion(
            paciente, primera_sesion.escalas_en_sesion,
        )
        primera_sesion.graficos_escalas_json = json.dumps(
            primera_sesion.graficos_escalas, ensure_ascii=False,
        )
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'primera_sesion': primera_sesion,
        'sesiones_posteriores': sesiones_posteriores,
        'hay_sesiones': sesiones.exists(),
        'total_sesiones': sesiones.count(),
    }

    registrar_auditoria(
        request, 'consulta_lista_sesiones_kine', paciente,
        detalle=f'Listado sesiones kinésicas — {paciente.rut}',
    )
    
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
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Verificar que no exista una primera sesión
    if SesionKinesica.objects.filter(paciente=paciente, es_primera_sesion=True).exists():
        messages.warning(request, 'Este paciente ya tiene una sesión inicial. Crea una sesión de seguimiento.')
        return redirect('listar_sesiones_kinesicas', rut=rut_paciente)
    
    if request.method == 'POST':
        if _rechazar_texto_marcado(request, request.POST, incluir_evaluacion=True):
            return render(request, 'SesionesKinesicas/crear_primera_sesion.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
            })
        try:
            evaluacion_datos = evaluacion_inicial_desde_post(request.POST)
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

            registrar_auditoria(
                request, 'alta_sesion_kine', paciente,
                detalle='Sesión kinésica inicial (#1)',
            )
            
            messages.success(request, 'Primera sesión kinésica creada exitosamente.')
            from django.urls import reverse
            return redirect(f"{reverse('sesiones_kinesicas:ver')}?rut={rut_paciente}&numero_sesion=1")
            
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
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Verificar que exista una primera sesión
    if not SesionKinesica.objects.filter(paciente=paciente, es_primera_sesion=True).exists():
        messages.error(request, 'Primero debes crear una sesión inicial.')
        return redirect('crear_primera_sesion_kinesica', rut=rut_paciente)
    
    if request.method == 'POST':
        if _rechazar_texto_marcado(request, request.POST):
            ultima_sesion = SesionKinesica.objects.filter(
                paciente=paciente
            ).order_by('-numero_sesion').first()
            return render(request, 'SesionesKinesicas/crear_sesion_seguimiento.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
                'ultima_sesion': ultima_sesion,
                'proximo_numero': (ultima_sesion.numero_sesion + 1) if ultima_sesion else 2,
            })
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

            registrar_auditoria(
                request, 'alta_sesion_kine', paciente,
                detalle=f'Sesión kinésica de seguimiento (#{nuevo_numero})',
            )
            
            messages.success(request, f'Sesión #{nuevo_numero} creada exitosamente.')
            from django.urls import reverse
            return redirect(f"{reverse('sesiones_kinesicas:ver')}?rut={rut_paciente}&numero_sesion={nuevo_numero}")
            
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
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('listar_sesiones_kinesicas')
    
    # Obtener la sesión
    sesion = get_object_or_404(
        SesionKinesica,
        paciente=paciente,
        numero_sesion=numero_sesion
    )
    
    escalas_en_sesion = RegistroEscalaSesion.objects.filter(
        sesion_kinesica=sesion
    ).order_by('-fecha_registro')
    
    graficos_escalas = graficos_para_registros_sesion(paciente, escalas_en_sesion)

    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'sesion': sesion,
        'es_primera_sesion': sesion.es_primera_sesion,
        'escalas_en_sesion': escalas_en_sesion,
        'graficos_escalas': graficos_escalas,
        'graficos_escalas_json': json.dumps(graficos_escalas, ensure_ascii=False),
        'paquetes_escalas': paquetes_escalas_para_paciente(paciente.rut, sesion.numero_sesion),
    }

    registrar_auditoria(
        request, 'consulta_sesion_kine', paciente,
        detalle=f'Sesión kinésica #{numero_sesion}',
    )
    
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
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
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
        if _rechazar_texto_marcado(
            request,
            request.POST,
            incluir_evaluacion=sesion.es_primera_sesion,
            incluir_final=sesion.es_sesion_final,
        ):
            return render(request, 'SesionesKinesicas/editar_sesion.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'sesion': sesion,
                'es_primera_sesion': sesion.es_primera_sesion,
                'rut': rut_paciente,
            })
        try:
            # Actualizar notas y evolución (campos comunes a todas las sesiones)
            sesion.notas_clinicas = request.POST.get('notas_clinicas', '')
            sesion.evolucion = request.POST.get('evolucion', '')
            
            # Si es la primera sesión, actualizar también la evaluación inicial
            if sesion.es_primera_sesion:
                sesion.evaluacion_inicial = evaluacion_inicial_desde_post(request.POST)
            
            # Si es sesión final, guardar sus campos específicos
            if sesion.es_sesion_final:
                sesion.diagnostico_final = request.POST.get('diagnostico_final', '') or sesion.diagnostico_final
                sesion.resumen_tratamiento = request.POST.get('resumen_tratamiento', '') or sesion.resumen_tratamiento
                sesion.logros_obtenidos = request.POST.get('logros_obtenidos', '') or sesion.logros_obtenidos
                sesion.estado_al_alta = request.POST.get('estado_al_alta', '') or sesion.estado_al_alta
                sesion.recomendaciones_alta = request.POST.get('recomendaciones_alta', '') or sesion.recomendaciones_alta
                sesion.plan_seguimiento = request.POST.get('plan_seguimiento', '') or sesion.plan_seguimiento
            
            sesion.save()
            registrar_auditoria(
                request, 'edicion_sesion_kine', paciente,
                detalle=f'Editó sesión kinésica #{numero_sesion}',
            )
            messages.success(request, 'Sesión actualizada exitosamente.')
            from django.urls import reverse
            return redirect(f"{reverse('sesiones_kinesicas:ver')}?rut={rut_paciente}&numero_sesion={numero_sesion}")
            
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


@requiere_clinico
def crear_sesion_final(request):
    """
    Crea una sesión final/de cierre del tratamiento.
    Incluye diagnóstico kinésico, resumen, logros, estado al alta y recomendaciones.
    NO bloquea la creación de sesiones futuras.
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
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('sesiones_kinesicas:listar')
    
    # Verificar que exista al menos una sesión previa
    if not SesionKinesica.objects.filter(paciente=paciente).exists():
        messages.error(request, 'Debe existir al menos una sesión antes de crear la sesión final.')
        return redirect('sesiones_kinesicas:listar')
    
    if request.method == 'POST':
        if _rechazar_texto_marcado(request, request.POST, incluir_final=True):
            ultima_sesion = SesionKinesica.objects.filter(
                paciente=paciente
            ).order_by('-numero_sesion').first()
            total_sesiones = SesionKinesica.objects.filter(paciente=paciente).count()
            return render(request, 'SesionesKinesicas/crear_sesion_final.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
                'ultima_sesion': ultima_sesion,
                'proximo_numero': (ultima_sesion.numero_sesion + 1) if ultima_sesion else 1,
                'total_sesiones': total_sesiones,
                'estado_choices': SesionKinesica.ESTADO_ALTA_CHOICES,
            })
        try:
            # Obtener el siguiente número de sesión
            ultima_sesion = SesionKinesica.objects.filter(
                paciente=paciente
            ).order_by('-numero_sesion').first()
            nuevo_numero = (ultima_sesion.numero_sesion if ultima_sesion else 0) + 1
            
            notas = request.POST.get('notas_clinicas', '')
            evolucion = request.POST.get('evolucion', '')
            diagnostico_final = request.POST.get('diagnostico_final', '')
            resumen_tratamiento = request.POST.get('resumen_tratamiento', '')
            logros_obtenidos = request.POST.get('logros_obtenidos', '')
            estado_al_alta = request.POST.get('estado_al_alta', '')
            recomendaciones_alta = request.POST.get('recomendaciones_alta', '')
            plan_seguimiento = request.POST.get('plan_seguimiento', '')
            
            # Crear la sesión final
            sesion = SesionKinesica.objects.create(
                paciente=paciente,
                clinico=clinico_obj if not es_admin else Clinico.objects.first(),
                numero_sesion=nuevo_numero,
                es_primera_sesion=False,
                es_sesion_final=True,
                notas_clinicas=notas,
                evolucion=evolucion,
                diagnostico_final=diagnostico_final,
                resumen_tratamiento=resumen_tratamiento,
                logros_obtenidos=logros_obtenidos,
                estado_al_alta=estado_al_alta,
                recomendaciones_alta=recomendaciones_alta,
                plan_seguimiento=plan_seguimiento,
            )

            registrar_auditoria(
                request, 'alta_sesion_kine', paciente,
                detalle=f'Sesión kinésica final (#{nuevo_numero})',
            )
            
            messages.success(request, f'Sesión final #{nuevo_numero} creada exitosamente.')
            # Notificar alta al paciente y clínico por correo
            clinico_para_email = clinico_obj if clinico_obj else Clinico.objects.first()
            notificar_alta_paciente(paciente, clinico_para_email, sesion)
            from django.urls import reverse
            return redirect(f"{reverse('sesiones_kinesicas:ver')}?rut={rut_paciente}&numero_sesion={nuevo_numero}")
            
        except Exception as e:
            messages.error(request, f'Error al crear la sesión final: {str(e)}')
    
    # Obtener info para el contexto
    ultima_sesion = SesionKinesica.objects.filter(
        paciente=paciente
    ).order_by('-numero_sesion').first()
    
    total_sesiones = SesionKinesica.objects.filter(paciente=paciente).count()
    
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'rut': rut_paciente,
        'ultima_sesion': ultima_sesion,
        'proximo_numero': (ultima_sesion.numero_sesion + 1) if ultima_sesion else 1,
        'total_sesiones': total_sesiones,
        'estado_choices': SesionKinesica.ESTADO_ALTA_CHOICES,
    }
    
    return render(request, 'SesionesKinesicas/crear_sesion_final.html', context)


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
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        sesiones = SesionKinesica.objects.filter(paciente=paciente).order_by('-numero_sesion')
        
        sesiones_data = [
            {
                'numero_sesion': s.numero_sesion,
                'fecha': s.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'es_primera': s.es_primera_sesion,
                'es_final': s.es_sesion_final,
                'tipo': 'Evaluación Inicial' if s.es_primera_sesion else ('Sesión Final' if s.es_sesion_final else f'Sesión #{s.numero_sesion}'),
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
