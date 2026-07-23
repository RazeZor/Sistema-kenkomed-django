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
from ciclos_clinicos.context_helpers import contexto_ciclo_para_template
from .session_inputs import evaluacion_inicial_desde_post, validar_post_sesion_kinesica
from .models import SesionKinesica, RegistroEscalaSesion
from .escalas_sesion import obtener_escalas_agrupadas_por_numero, paquetes_escalas_para_ciclo
from .ciclo_helpers import (
    asegurar_editable,
    filtrar_sesiones,
    finalizar_ciclo_si_sesion_final,
    redirect_listar,
    redirect_ver,
    resolver_ciclo,
)
from .ux_helpers import contexto_tratamiento_ux
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


def _ctx_tratamiento(request, paciente, ciclo, sesiones_qs=None):
    if sesiones_qs is None and ciclo:
        sesiones_qs = filtrar_sesiones(ciclo)
    return contexto_tratamiento_ux(request, paciente, ciclo, sesiones_qs)


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
    clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
    
    # Obtener el paciente
    try:
        paciente = obtener_paciente_con_permiso(rut_paciente, request)
        if not paciente:
            raise Paciente.DoesNotExist()
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return redirect('historialClinico')
    
    ciclo = resolver_ciclo(request, paciente, clinico_obj)
    if not ciclo:
        messages.error(request, 'No hay ciclo clínico seleccionado.')
        return redirect('historialClinico')
    
    sesiones = filtrar_sesiones(ciclo)
    sesiones_timeline = list(filtrar_sesiones(ciclo, ascendente=True))
    primera_sesion = sesiones.filter(es_primera_sesion=True).first()
    sesiones_posteriores = list(sesiones.filter(es_primera_sesion=False))
    tiene_sesion_final = sesiones.filter(es_sesion_final=True).exists()
    escalas_por_numero = obtener_escalas_agrupadas_por_numero(ciclo)
    for s in sesiones_timeline:
        s.escalas_en_sesion = escalas_por_numero.get(s.numero_sesion, [])
    
    ctx_ciclo = contexto_ciclo_para_template(ciclo, paciente)
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'ciclo': ciclo,
        'primera_sesion': primera_sesion,
        'sesiones_posteriores': sesiones_posteriores,
        'sesiones_timeline': sesiones_timeline,
        'hay_sesiones': sesiones.exists(),
        'total_sesiones': sesiones.count(),
        'tiene_sesion_final': tiene_sesion_final,
        'paquetes_escalas': paquetes_escalas_para_ciclo(paciente.rut, ciclo),
        **ctx_ciclo,
        **_ctx_tratamiento(request, paciente, ciclo, sesiones),
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
        return redirect(redirect_listar(rut_paciente or ''))
    
    ciclo = resolver_ciclo(request, paciente, clinico_obj, crear_si_ausente=True)
    if not ciclo:
        messages.error(request, 'No se pudo iniciar el ciclo clínico.')
        return redirect('historialClinico')
    
    if not asegurar_editable(request, ciclo):
        return redirect(redirect_listar(rut_paciente, ciclo))
    
    # Verificar que no exista una primera sesión en este ciclo
    if filtrar_sesiones(ciclo).filter(es_primera_sesion=True).exists():
        messages.warning(request, 'Este ciclo ya tiene una sesión inicial. Crea una sesión de seguimiento.')
        return redirect(redirect_listar(rut_paciente, ciclo))
    
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
                ciclo=ciclo,
                clinico=clinico_obj if not es_admin else Clinico.objects.first(),
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
            return redirect(redirect_ver(rut_paciente, 1, ciclo))
            
        except Exception as e:
            messages.error(request, f'Error al crear la sesión: {str(e)}')
            return render(request, 'SesionesKinesicas/crear_primera_sesion.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
            })
    
    sesiones = filtrar_sesiones(ciclo)
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'rut': rut_paciente,
        **contexto_ciclo_para_template(ciclo, paciente),
        **_ctx_tratamiento(request, paciente, ciclo, sesiones),
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
        return redirect(redirect_listar(rut_paciente or ''))
    
    ciclo = resolver_ciclo(request, paciente, clinico_obj, crear_si_ausente=True)
    if not ciclo:
        messages.error(request, 'No hay ciclo clínico activo.')
        return redirect('historialClinico')
    
    sesiones_ciclo = filtrar_sesiones(ciclo)
    if not sesiones_ciclo.filter(es_primera_sesion=True).exists():
        messages.error(request, 'Primero debes crear una sesión inicial en este ciclo.')
        from django.urls import reverse
        url = f"{reverse('sesiones_kinesicas:crear_primera')}?rut={rut_paciente}&ciclo_id={ciclo.id}"
        return redirect(url)
    
    if not asegurar_editable(request, ciclo):
        return redirect(redirect_listar(rut_paciente, ciclo))
    
    if request.method == 'POST':
        if _rechazar_texto_marcado(request, request.POST):
            ultima_sesion = sesiones_ciclo.first()
            return render(request, 'SesionesKinesicas/crear_sesion_seguimiento.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
                'ultima_sesion': ultima_sesion,
                'proximo_numero': (ultima_sesion.numero_sesion + 1) if ultima_sesion else 2,
                **contexto_ciclo_para_template(ciclo, paciente),
            })
        try:
            ultima_sesion = sesiones_ciclo.first()
            nuevo_numero = (ultima_sesion.numero_sesion if ultima_sesion else 0) + 1
            
            notas = request.POST.get('notas_clinicas', '')
            evolucion = request.POST.get('evolucion', '')
            
            SesionKinesica.objects.create(
                paciente=paciente,
                ciclo=ciclo,
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
            return redirect(redirect_ver(rut_paciente, nuevo_numero, ciclo))
            
        except Exception as e:
            messages.error(request, f'Error al crear la sesión: {str(e)}')
    
    ultima_sesion = sesiones_ciclo.first()
    proximo_numero = (ultima_sesion.numero_sesion + 1) if ultima_sesion else 2

    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'rut': rut_paciente,
        'ultima_sesion': ultima_sesion,
        'proximo_numero': proximo_numero,
        'paquetes_escalas': paquetes_escalas_para_ciclo(paciente.rut, ciclo, proximo_numero),
        **contexto_ciclo_para_template(ciclo, paciente),
        **_ctx_tratamiento(request, paciente, ciclo, sesiones_ciclo),
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
        return redirect(redirect_listar(rut_paciente or ''))
    
    ciclo = resolver_ciclo(request, paciente, clinico_obj)
    if not ciclo:
        messages.error(request, 'No hay ciclo clínico seleccionado.')
        return redirect('historialClinico')
    
    sesion = get_object_or_404(
        SesionKinesica,
        ciclo=ciclo,
        numero_sesion=numero_sesion,
    )
    
    escalas_en_sesion = RegistroEscalaSesion.objects.filter(
        sesion_kinesica=sesion
    ).order_by('-fecha_registro')
    
    graficos_escalas = graficos_para_registros_sesion(ciclo, escalas_en_sesion)

    ctx_ciclo = contexto_ciclo_para_template(ciclo, paciente)
    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'sesion': sesion,
        'es_primera_sesion': sesion.es_primera_sesion,
        'escalas_en_sesion': escalas_en_sesion,
        'graficos_escalas': graficos_escalas,
        'graficos_escalas_json': json.dumps(graficos_escalas, ensure_ascii=False),
        'paquetes_escalas': paquetes_escalas_para_ciclo(paciente.rut, ciclo, sesion.numero_sesion),
        'abrir_edicion': request.GET.get('edit') == '1',
        **ctx_ciclo,
        **_ctx_tratamiento(request, paciente, ciclo, filtrar_sesiones(ciclo)),
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
        return redirect(redirect_listar(rut_paciente or ''))
    
    ciclo = resolver_ciclo(request, paciente, clinico_obj)
    if not ciclo:
        messages.error(request, 'No hay ciclo clínico seleccionado.')
        return redirect('historialClinico')
    
    sesion = get_object_or_404(
        SesionKinesica,
        ciclo=ciclo,
        numero_sesion=numero_sesion,
    )

    if request.method == 'GET':
        return redirect(f"{redirect_ver(rut_paciente, numero_sesion, ciclo)}&edit=1")
    
    if request.method == 'POST':
        if not asegurar_editable(request, ciclo):
            return redirect(redirect_ver(rut_paciente, numero_sesion, ciclo))
        if _rechazar_texto_marcado(
            request,
            request.POST,
            incluir_evaluacion=sesion.es_primera_sesion,
            incluir_final=sesion.es_sesion_final,
        ):
            return redirect(f"{redirect_ver(rut_paciente, numero_sesion, ciclo)}&edit=1")
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
            return redirect(redirect_ver(rut_paciente, numero_sesion, ciclo))
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la sesión: {str(e)}')
    
    return redirect(redirect_ver(rut_paciente, numero_sesion, ciclo))


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
        return redirect(redirect_listar(rut_paciente or ''))
    
    ciclo = resolver_ciclo(request, paciente, clinico_obj, crear_si_ausente=True)
    if not ciclo:
        messages.error(request, 'No hay ciclo clínico activo.')
        return redirect('historialClinico')
    
    sesiones_ciclo = filtrar_sesiones(ciclo)
    if not sesiones_ciclo.exists():
        messages.error(request, 'Debe existir al menos una sesión antes de crear la sesión final.')
        return redirect(redirect_listar(rut_paciente, ciclo))
    
    if not asegurar_editable(request, ciclo):
        return redirect(redirect_listar(rut_paciente, ciclo))
    
    if request.method == 'POST':
        if _rechazar_texto_marcado(request, request.POST, incluir_final=True):
            ultima_sesion = sesiones_ciclo.first()
            return render(request, 'SesionesKinesicas/crear_sesion_final.html', {
                'nombre_clinico': nombre_clinico,
                'paciente': paciente,
                'rut': rut_paciente,
                'ultima_sesion': ultima_sesion,
                'proximo_numero': (ultima_sesion.numero_sesion + 1) if ultima_sesion else 1,
                'total_sesiones': sesiones_ciclo.count(),
                'estado_choices': SesionKinesica.ESTADO_ALTA_CHOICES,
                **contexto_ciclo_para_template(ciclo, paciente),
            })
        try:
            ultima_sesion = sesiones_ciclo.first()
            nuevo_numero = (ultima_sesion.numero_sesion if ultima_sesion else 0) + 1
            
            notas = request.POST.get('notas_clinicas', '')
            evolucion = request.POST.get('evolucion', '')
            diagnostico_final = request.POST.get('diagnostico_final', '')
            resumen_tratamiento = request.POST.get('resumen_tratamiento', '')
            logros_obtenidos = request.POST.get('logros_obtenidos', '')
            estado_al_alta = request.POST.get('estado_al_alta', '')
            recomendaciones_alta = request.POST.get('recomendaciones_alta', '')
            plan_seguimiento = request.POST.get('plan_seguimiento', '')
            
            sesion = SesionKinesica.objects.create(
                paciente=paciente,
                ciclo=ciclo,
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

            finalizar_ciclo_si_sesion_final(request, sesion, clinico_obj)

            registrar_auditoria(
                request, 'alta_sesion_kine', paciente,
                detalle=f'Sesión kinésica final (#{nuevo_numero})',
            )
            
            messages.success(request, f'Sesión final #{nuevo_numero} creada exitosamente. Ciclo clínico finalizado.')
            clinico_para_email = clinico_obj if clinico_obj else Clinico.objects.first()
            notificar_alta_paciente(paciente, clinico_para_email, sesion)
            return redirect(redirect_ver(rut_paciente, nuevo_numero, ciclo))
            
        except Exception as e:
            messages.error(request, f'Error al crear la sesión final: {str(e)}')
    
    ultima_sesion = sesiones_ciclo.first()
    proximo_numero = (ultima_sesion.numero_sesion + 1) if ultima_sesion else 1

    context = {
        'nombre_clinico': nombre_clinico,
        'paciente': paciente,
        'rut': rut_paciente,
        'ultima_sesion': ultima_sesion,
        'proximo_numero': proximo_numero,
        'total_sesiones': sesiones_ciclo.count(),
        'estado_choices': SesionKinesica.ESTADO_ALTA_CHOICES,
        'paquetes_escalas': paquetes_escalas_para_ciclo(paciente.rut, ciclo, proximo_numero),
        **contexto_ciclo_para_template(ciclo, paciente),
        **_ctx_tratamiento(request, paciente, ciclo, sesiones_ciclo),
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
        if not paciente:
            raise Paciente.DoesNotExist()
        rut_clinico = request.session.get('rut_clinico')
        clinico_obj = Clinico.objects.filter(rut=rut_clinico).first() if rut_clinico else None
        ciclo = resolver_ciclo(request, paciente, clinico_obj)
        if not ciclo:
            return JsonResponse({'error': 'Sin ciclo clínico'}, status=404)
        sesiones = filtrar_sesiones(ciclo)
        
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
