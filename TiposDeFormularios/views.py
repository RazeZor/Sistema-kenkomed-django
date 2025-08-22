import json
from django.shortcuts import render, get_object_or_404,redirect
from django.urls import reverse
from Login.models import formularioClinico, Paciente,CuestionarioPSFS,Groc,Clinico,CuestionarioEQ_5D,CuestionarioBarthel
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime


def RenderizarGROC(request):
    rut = request.GET.get('rut', '')
    paciente = get_object_or_404(Paciente, rut=rut)

    # Verificamos si ya existe una evaluación en la tabla Groc para este paciente
    evaluacion_existente = Groc.objects.filter(paciente=paciente).exists()

    # Obtener los puntajes del paciente, si existe una evaluación
    puntajes = []
    if evaluacion_existente:
        # Obtiene los puntajes de la evaluación del paciente
        groc_obj = Groc.objects.get(paciente=paciente)
        puntajes = groc_obj.puntajeGroc  # Esto devuelve una lista de diccionarios
        NotaGroc = groc_obj.NotaGroc  # Asignamos NotaGroc si existe una evaluacion
    else:   
        NotaGroc = "el Paciente No tiene Notas"  # Si no existe la evaluación, asignamos un valor predeterminado

    if request.method == 'POST':
        fecha_creacion = datetime.now().date()
        puntajeGroc = request.POST.get('puntajeGroc')  # Valor único de la escala
        NotaGroc = request.POST.get('nota_adicional')  # Actualizamos NotaGroc con el valor del formulario
        action = request.POST.get('action', '')  # Obtenemos la acción

        # Validar campos
        if not puntajeGroc:
            messages.error(request, "Todos los campos son obligatorios.")
            return render(request, 'GROC.html', {'rut': rut, 'paciente': paciente, 'evaluacion_existente': evaluacion_existente, 'puntajes': puntajes, 'NotaGroc': NotaGroc})

        if action == 'guardar':
            # Acción de guardar (si no existe una evaluación anterior)
            Groc.objects.create(
                paciente=paciente,
                fecha_creacion=fecha_creacion,
                NotaGroc=NotaGroc,
                puntajeGroc=[{'puntaje': int(puntajeGroc)}]  # Guardamos el primer puntaje en la lista
            )
            messages.success(request, "Evaluación registrada correctamente.")
            return HttpResponseRedirect(request.get_full_path())  # Recarga la página actual

        elif action == 'actualizar':
            try:
                evaluacion = Groc.objects.get(paciente=paciente)
                
                if isinstance(evaluacion.puntajeGroc, list):
                    evaluacion.puntajeGroc.append({'puntaje': int(puntajeGroc)})
                else:
                    evaluacion.puntajeGroc = [{'puntaje': int(puntajeGroc)}]

                evaluacion.save()
                messages.success(request, "Evaluación actualizada correctamente.")
            except Groc.DoesNotExist:
                messages.error(request, "No se encontró la evaluación para actualizar.")
            return HttpResponseRedirect(request.get_full_path())  # Recarga la página actual
        elif action == 'GuardarNota':
            try:
                evaluacion = Groc.objects.get(paciente=paciente)
                evaluacion.NotaGroc = NotaGroc
                evaluacion.save()

                messages.success(request, "Nota actualizada correctamente.")
            except Groc.DoesNotExist:
                messages.error(request, "No se encontró la evaluación para actualizar la nota.")
            
            return HttpResponseRedirect(request.get_full_path())  # Recarga la página actual


    return render(request, 'GROC.html', {
        'rut': rut,
        'paciente': paciente,
        'evaluacion_existente': evaluacion_existente,
        'puntajes': puntajes,
        'NotaGroc': NotaGroc  # Asegúrate de pasar NotaGroc al contexto
    })

def gestionar_psfs(request):
    try:
        rut = request.GET.get('rut', '') or request.POST.get('rut', '')
        paciente = get_object_or_404(Paciente, rut=rut)
        action = request.POST.get('action', '')
         # Verificar si ya existen sesiones registradas
        sesiones = CuestionarioPSFS.objects.filter(paciente=paciente)
        sesiones_existentes = sesiones.exists()
        
        if request.method == 'POST':
            puntaje_actividad_1 = request.POST.getlist('rango1')
            puntaje_actividad_2 = request.POST.getlist('rango2')
            puntaje_actividad_3 = request.POST.getlist('rango3')
            puntajeTotal = request.POST.getlist('total_score')
            notaPSFS = request.POST.get('notes')
            
            if action == 'guardar':
                cuestionario = CuestionarioPSFS.objects.create(
                    paciente=paciente,
                    fecha_creacion=datetime.now().date(),
                    puntaje_actividad_1=json.dumps(puntaje_actividad_1),
                    puntaje_actividad_2=json.dumps(puntaje_actividad_2),
                    puntaje_actividad_3=json.dumps(puntaje_actividad_3),
                    puntajeTotal=json.dumps(puntajeTotal),
                )
                cuestionario.save()
                messages.success(request, "Cuestionario guardado correctamente.")
                return redirect(f"{reverse('gestionar_psfs')}?rut={rut}")
                
            elif action == 'actualizar':
                cuestionario = CuestionarioPSFS.objects.filter(paciente=paciente).first()
                if cuestionario:
                    actividad_1_actual = json.loads(cuestionario.puntaje_actividad_1) if cuestionario.puntaje_actividad_1 else []
                    actividad_2_actual = json.loads(cuestionario.puntaje_actividad_2) if cuestionario.puntaje_actividad_2 else []
                    actividad_3_actual = json.loads(cuestionario.puntaje_actividad_3) if cuestionario.puntaje_actividad_3 else []
                    total_actual = json.loads(cuestionario.puntajeTotal) if cuestionario.puntajeTotal else []

                    # Agregar sin sobrescribir
                    actividad_1_actual.extend(puntaje_actividad_1)
                    actividad_2_actual.extend(puntaje_actividad_2)
                    actividad_3_actual.extend(puntaje_actividad_3)
                    total_actual.extend(puntajeTotal)

                    cuestionario.puntaje_actividad_1 = json.dumps(actividad_1_actual)
                    cuestionario.puntaje_actividad_2 = json.dumps(actividad_2_actual)
                    cuestionario.puntaje_actividad_3 = json.dumps(actividad_3_actual)
                    cuestionario.puntajeTotal = json.dumps(total_actual)
                    cuestionario.save()
                    messages.success(request, "Cuestionario actualizado correctamente.")
                    return redirect(f"{reverse('gestionar_psfs')}?rut={rut}")

                else:
                    return HttpResponse('No hay un cuestionario existente para actualizar.', status=404)
            
            # Guardar o actualizar la nota
            if notaPSFS:
                EvaluacionExistente = CuestionarioPSFS.objects.filter(paciente=paciente).first()
                if EvaluacionExistente:
                    EvaluacionExistente.NotaCuestionarioPSFS = notaPSFS
                    EvaluacionExistente.save()
                    messages.success(request, "Nota actualizada correctamente.")
                    return redirect(f"{reverse('gestionar_psfs')}?rut={rut}")

                else:
                    return HttpResponse("No hay un cuestionario para actualizar la nota.", status=404)
                    
            
        
        # Renderizar PSFS
        formularios = formularioClinico.objects.filter(paciente=paciente)
        cuestionario = CuestionarioPSFS.objects.filter(paciente=paciente).first()
        evaluacion_existente = CuestionarioPSFS.objects.filter(paciente=paciente).exists()
        nota = cuestionario.NotaCuestionarioPSFS if cuestionario else None
        
        if cuestionario:
            puntajes_actividad_1 = json.loads(cuestionario.puntaje_actividad_1) if cuestionario.puntaje_actividad_1 else []
            puntajes_actividad_2 = json.loads(cuestionario.puntaje_actividad_2) if cuestionario.puntaje_actividad_2 else []
            puntajes_actividad_3 = json.loads(cuestionario.puntaje_actividad_3) if cuestionario.puntaje_actividad_3 else []
            puntajes_total = json.loads(cuestionario.puntajeTotal) if cuestionario.puntajeTotal else []

            sesiones = []
            for i in range(len(puntajes_actividad_1)):
                sesiones.append({
                    "sesion": i + 1,
                    "actividad_1": puntajes_actividad_1[i] if i < len(puntajes_actividad_1) else "-",
                    "actividad_2": puntajes_actividad_2[i] if i < len(puntajes_actividad_2) else "-",
                    "actividad_3": puntajes_actividad_3[i] if i < len(puntajes_actividad_3) else "-",
                    "total": puntajes_total[i] if i < len(puntajes_total) else "-",
                })
        else:
            sesiones = []

        if formularios.exists():
            formulario = formularios.first()  
            actividades = json.loads(formulario.actividades_afectadas) 
            
            actividad1 = actividades[0] if len(actividades) > 0 else ''
            actividad2 = actividades[1] if len(actividades) > 1 else ''
            actividad3 = actividades[2] if len(actividades) > 2 else ''
        else:
            actividad1 = actividad2 = actividad3 = ''

        return render(request, 'CuestionarioPSFS.html', {
            'rut': rut, 
            'actividad1': actividad1,
            'actividad2': actividad2,
            'actividad3': actividad3,
            'sesiones_existentes': sesiones_existentes,
            'sesiones': sesiones,
            'evaluacion_existente': evaluacion_existente,
            'nota': nota
        })
    
    except ValueError:
        return HttpResponse('YA EXISTEN DATOS', status=404)
    except Exception as e:
        return HttpResponse(f'Error inesperado: {str(e)}', status=500)

def RenderizarEQ_5D(request):
    
    
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)
        rut_clinico = request.session.get('rut_clinico')
        
        if not rut_clinico:
            messages.error(request, 'Debe haber un inicio de sesión para estar aquí...')
            return redirect('login')

        try:
            clinico = Clinico.objects.get(rut=rut_clinico)
        except Clinico.DoesNotExist:
            messages.error(request, 'El clínico no está en el sistema, intenta nuevamente...')
            return redirect('login')

        rut = request.GET.get('rut', '') or request.POST.get('rut', '')
        paciente = get_object_or_404(Paciente, rut=rut)
        sesiones = CuestionarioEQ_5D.objects.filter(paciente=paciente)
        sesiones_existentes = sesiones.exists()

        if request.method == 'POST':
            action = request.POST.get('action')
            if action == 'actualizar':
                cuestionario, created = CuestionarioEQ_5D.objects.get_or_create(paciente=paciente)
                
                # Obtener los nuevos valores
                nuevos_valores = {
                    'puntaje_movilidad': request.POST.get('puntaje_movilidad'),
                    'puntaje_cuidado_personal': request.POST.get('puntaje_cuidado_personal'),
                    'puntaje_actividades_cotidianas': request.POST.get('puntaje_actividades_cotidianas'),
                    'puntaje_dolor_malestar': request.POST.get('puntaje_dolor_malestar'),
                    'puntaje_ansiedad_depresion': request.POST.get('puntaje_ansiedad_depresion'),
                    'vas_score': request.POST.get('vasScore')
                }
                
                # Actualizar cada campo JsonField
                for campo, valor in nuevos_valores.items():
                    valores_actuales = getattr(cuestionario, campo)
                    valores_actuales.append(valor)
                    setattr(cuestionario, campo, valores_actuales)
                
                cuestionario.save()
                messages.success(request, 'El cuestionario se ha actualizado correctamente.')
                return HttpResponseRedirect(request.get_full_path())
            elif action == 'guardar':
                movilidad = request.POST.getlist('movilidad')
                cuidado_personal = request.POST.getlist('cuidadoPersonal')
                actividades_cotidianas = request.POST.getlist('actividadesCotidianas')
                dolor_malestar = request.POST.getlist('dolorMalestar')
                ansiedad_depresion = request.POST.getlist('ansiedadDepresion')
                puntaje_movilidad = request.POST.getlist('puntaje_movilidad', None)
                puntaje_cuidado_personal = request.POST.getlist('puntaje_cuidado_personal', None)
                puntaje_actividades_cotidianas = request.POST.getlist('puntaje_actividades_cotidianas', None)
                puntaje_dolor_malestar = request.POST.getlist('puntaje_dolor_malestar', None)
                puntaje_ansiedad_depresion = request.POST.getlist('puntaje_ansiedad_depresion', None)
                vas_score = request.POST.getlist('vasScore', None)

                cuestionario = CuestionarioEQ_5D(
                    paciente=paciente,
                    clinico=clinico,
                    movilidad=movilidad,
                    cuidado_personal=cuidado_personal,
                    actividades_cotidianas=actividades_cotidianas,
                    dolor_malestar=dolor_malestar,
                    ansiedad_depresion=ansiedad_depresion,
                    puntaje_movilidad=puntaje_movilidad,
                    puntaje_cuidado_personal=puntaje_cuidado_personal,
                    puntaje_actividades_cotidianas=puntaje_actividades_cotidianas,
                    puntaje_dolor_malestar=puntaje_dolor_malestar,
                    puntaje_ansiedad_depresion=puntaje_ansiedad_depresion,
                    vas_score=vas_score
                )
                cuestionario.save()
                messages.success(request, 'El cuestionario se ha guardado correctamente.')
                return HttpResponseRedirect(request.get_full_path())

        # Mover esta parte fuera del if POST para que siempre se ejecute
        historial_evaluaciones = CuestionarioEQ_5D.objects.filter(paciente=paciente)

        # Verificar si hay evaluaciones
        if historial_evaluaciones.exists():
            # Preparar datos para la tabla
            puntajes_por_sesion = []

            # Verificar si hay datos en vas_score antes de usar max()
            max_length = max((len(evaluacion.vas_score) for evaluacion in historial_evaluaciones), default=0)

            for i in range(max_length):
                for evaluacion in historial_evaluaciones:
                    if i < len(evaluacion.vas_score):  # Verificar si hay un puntaje en este índice
                        puntajes_por_sesion.append({
                            'sesion': f'{len(puntajes_por_sesion) // len(historial_evaluaciones) + 1}',
                            'vas_score': evaluacion.vas_score[i], 
                            'movilidad': evaluacion.puntaje_movilidad[i],
                            'cuidado_personal': evaluacion.puntaje_cuidado_personal[i],
                            'actividades_cotidianas': evaluacion.puntaje_actividades_cotidianas[i],
                            'dolor_malestar': evaluacion.puntaje_dolor_malestar[i],
                            'ansiedad_depresion': evaluacion.puntaje_ansiedad_depresion[i]
                        })
        else:
            puntajes_por_sesion = []  

        # Siempre se ejecuta este render
        return render(request, 'CuestionarioEQ-5D.html', {
            'rut': rut,
            'puntajes_por_sesion': puntajes_por_sesion,
            'paciente': paciente,
            'sesiones_existentes': sesiones_existentes
        })
    else:
        messages.error(request, 'Debe haber un inicio de sesión para acceder a esta página.')
        return redirect('login')




def renderizar_CuestionarioBarthel(request):
    if 'nombre_clinico' not in request.session:
        messages.error(request, 'Debe haber un inicio de sesión para acceder a esta página.')
        return redirect('login')
    
    nombre_clinico = request.session['nombre_clinico']
    es_admin = request.session.get('es_admin', False)
    rut_clinico = request.session.get('rut_clinico')
    
    if not rut_clinico:
        messages.error(request, 'Debe haber un inicio de sesión para estar aquí...')
        return redirect('login')

    try:
        clinico = Clinico.objects.get(rut=rut_clinico)
    except Clinico.DoesNotExist:
        messages.error(request, 'El clínico no está en el sistema, intenta nuevamente...')
        return redirect('login')

    # Obtener parámetros
    rut_paciente = request.GET.get('rut', '') or request.POST.get('rut', '')
    paciente = None
    
    if rut_paciente:
        try:
            paciente = Paciente.objects.get(rut=rut_paciente)
        except Paciente.DoesNotExist:
            messages.error(request, 'Paciente no encontrado.')
            return redirect('bartel')

    if request.method == "POST":
        # Si no hay paciente seleccionado, obtenerlo del formulario
        if not paciente:
            paciente_rut = request.POST.get("paciente")
            if paciente_rut:
                try:
                    paciente = Paciente.objects.get(rut=paciente_rut)
                except Paciente.DoesNotExist:
                    messages.error(request, "Paciente no encontrado.")
                    return redirect('bartel')
            else:
                messages.error(request, "Debe seleccionar un paciente.")
                return redirect('bartel')

        action = request.POST.get('action', '')
        notaBarthel = request.POST.get('nota_adicional', '')

        if action == 'guardar':
            # Campos esperados del cuestionario
            campos = [
                "comer", "lavarse", "vestirse", "arreglarse",
                "deposiciones", "miccion", "usar_retrete",
                "trasladarse", "deambular", "escalones"
            ]

            datos = {}
            for campo in campos:
                valor = request.POST.get(campo)
                if valor is None or valor == "":
                    messages.error(request, f"Falta el campo: {campo}")
                    return redirect('bartel')
                
                try:
                    v_int = int(valor)
                except ValueError:
                    messages.error(request, f"Valor inválido en {campo}")
                    return redirect('bartel')

                datos[campo] = v_int

            total = sum(datos.values())
            if datos.get("deambular") == 5 and total > 90:
                total = 90
            if total < 20:
                grado = "Total"
            elif total <= 35:
                grado = "Grave"
            elif total <= 55:
                grado = "Moderado"
            elif total < 100:
                grado = "Leve"
            else:
                grado = "Independiente"

            try:
                cuestionario = CuestionarioBarthel.objects.create(
                    paciente=paciente,
                    clinico=clinico,
                    fecha_creacion=datetime.now().date(),
                    comer=json.dumps([datos['comer']]),
                    lavarse=json.dumps([datos['lavarse']]),
                    vestirse=json.dumps([datos['vestirse']]),
                    arreglarse=json.dumps([datos['arreglarse']]),
                    deposiciones=json.dumps([datos['deposiciones']]),
                    miccion=json.dumps([datos['miccion']]),
                    usar_retrete=json.dumps([datos['usar_retrete']]),
                    trasladarse=json.dumps([datos['trasladarse']]),
                    deambular=json.dumps([datos['deambular']]),
                    escalones=json.dumps([datos['escalones']]),
                    puntaje_total=json.dumps([total]),
                    grado_dependencia=json.dumps([grado]),
                    NotaCuestionarioBarthel=notaBarthel
                )
                messages.success(request, f"Cuestionario Barthel guardado correctamente para {paciente.nombre}. Puntaje: {total}, Grado: {grado}")
                return redirect(f"{reverse('bartel')}?rut={paciente.rut}")

            except Exception as e:
                messages.error(request, f"Error al guardar el cuestionario: {str(e)}")
                return redirect('bartel')

        elif action == 'actualizar':
            try:
                cuestionario = CuestionarioBarthel.objects.get(paciente=paciente)
                
                # Campos esperados del cuestionario
                campos = [
                    "comer", "lavarse", "vestirse", "arreglarse",
                    "deposiciones", "miccion", "usar_retrete",
                    "trasladarse", "deambular", "escalones"
                ]

                datos = {}
                for campo in campos:
                    valor = request.POST.get(campo)
                    if valor is None or valor == "":
                        messages.error(request, f"Falta el campo: {campo}")
                        return redirect('bartel')
                    
                    try:
                        v_int = int(valor)
                    except ValueError:
                        messages.error(request, f"Valor inválido en {campo}")
                        return redirect('bartel')

                    datos[campo] = v_int

                total = sum(datos.values())
                if datos.get("deambular") == 5 and total > 90:
                    total = 90
                if total < 20:
                    grado = "Total"
                elif total <= 35:
                    grado = "Grave"
                elif total <= 55:
                    grado = "Moderado"
                elif total < 100:
                    grado = "Leve"
                else:
                    grado = "Independiente"

                # Obtener valores actuales y agregar nuevos
                comer_actual = json.loads(cuestionario.comer) if cuestionario.comer else []
                lavarse_actual = json.loads(cuestionario.lavarse) if cuestionario.lavarse else []
                vestirse_actual = json.loads(cuestionario.vestirse) if cuestionario.vestirse else []
                arreglarse_actual = json.loads(cuestionario.arreglarse) if cuestionario.arreglarse else []
                deposiciones_actual = json.loads(cuestionario.deposiciones) if cuestionario.deposiciones else []
                miccion_actual = json.loads(cuestionario.miccion) if cuestionario.miccion else []
                usar_retrete_actual = json.loads(cuestionario.usar_retrete) if cuestionario.usar_retrete else []
                trasladarse_actual = json.loads(cuestionario.trasladarse) if cuestionario.trasladarse else []
                deambular_actual = json.loads(cuestionario.deambular) if cuestionario.deambular else []
                escalones_actual = json.loads(cuestionario.escalones) if cuestionario.escalones else []
                puntaje_total_actual = json.loads(cuestionario.puntaje_total) if cuestionario.puntaje_total else []
                grado_dependencia_actual = json.loads(cuestionario.grado_dependencia) if cuestionario.grado_dependencia else []

                # Agregar nuevos valores
                comer_actual.append(datos['comer'])
                lavarse_actual.append(datos['lavarse'])
                vestirse_actual.append(datos['vestirse'])
                arreglarse_actual.append(datos['arreglarse'])
                deposiciones_actual.append(datos['deposiciones'])
                miccion_actual.append(datos['miccion'])
                usar_retrete_actual.append(datos['usar_retrete'])
                trasladarse_actual.append(datos['trasladarse'])
                deambular_actual.append(datos['deambular'])
                escalones_actual.append(datos['escalones'])
                puntaje_total_actual.append(total)
                grado_dependencia_actual.append(grado)

                # Guardar actualización
                cuestionario.comer = json.dumps(comer_actual)
                cuestionario.lavarse = json.dumps(lavarse_actual)
                cuestionario.vestirse = json.dumps(vestirse_actual)
                cuestionario.arreglarse = json.dumps(arreglarse_actual)
                cuestionario.deposiciones = json.dumps(deposiciones_actual)
                cuestionario.miccion = json.dumps(miccion_actual)
                cuestionario.usar_retrete = json.dumps(usar_retrete_actual)
                cuestionario.trasladarse = json.dumps(trasladarse_actual)
                cuestionario.deambular = json.dumps(deambular_actual)
                cuestionario.escalones = json.dumps(escalones_actual)
                cuestionario.puntaje_total = json.dumps(puntaje_total_actual)
                cuestionario.grado_dependencia = json.dumps(grado_dependencia_actual)
                cuestionario.save()

                messages.success(request, f"Cuestionario Barthel actualizado correctamente para {paciente.nombre}. Puntaje: {total}, Grado: {grado}")
                return redirect(f"{reverse('bartel')}?rut={paciente.rut}")

            except CuestionarioBarthel.DoesNotExist:
                messages.error(request, "No se encontró el cuestionario para actualizar.")
                return redirect('bartel')
            except Exception as e:
                messages.error(request, f"Error al actualizar el cuestionario: {str(e)}")
                return redirect('bartel')

        elif action == 'GuardarNota':
            try:
                cuestionario = CuestionarioBarthel.objects.get(paciente=paciente)
                cuestionario.NotaCuestionarioBarthel = notaBarthel
                cuestionario.save()
                messages.success(request, "Nota actualizada correctamente.")
                return redirect(f"{reverse('bartel')}?rut={paciente.rut}")
            except CuestionarioBarthel.DoesNotExist:
                messages.error(request, "No se encontró el cuestionario para actualizar la nota.")
                return redirect('bartel')

    # GET: renderizar el formulario
    pacientes = Paciente.objects.all()
    clinicos = Clinico.objects.all()
    
    # Si hay un paciente específico, verificar si ya existe un cuestionario
    cuestionario_existente = None
    sesiones = []
    
    if paciente:
        try:
            cuestionario_existente = CuestionarioBarthel.objects.get(paciente=paciente)
        except CuestionarioBarthel.DoesNotExist:
            pass
        
        if cuestionario_existente:
            # Obtener datos de todas las sesiones
            comer = json.loads(cuestionario_existente.comer) if cuestionario_existente.comer else []
            lavarse = json.loads(cuestionario_existente.lavarse) if cuestionario_existente.lavarse else []
            vestirse = json.loads(cuestionario_existente.vestirse) if cuestionario_existente.vestirse else []
            arreglarse = json.loads(cuestionario_existente.arreglarse) if cuestionario_existente.arreglarse else []
            deposiciones = json.loads(cuestionario_existente.deposiciones) if cuestionario_existente.deposiciones else []
            miccion = json.loads(cuestionario_existente.miccion) if cuestionario_existente.miccion else []
            usar_retrete = json.loads(cuestionario_existente.usar_retrete) if cuestionario_existente.usar_retrete else []
            trasladarse = json.loads(cuestionario_existente.trasladarse) if cuestionario_existente.trasladarse else []
            deambular = json.loads(cuestionario_existente.deambular) if cuestionario_existente.deambular else []
            escalones = json.loads(cuestionario_existente.escalones) if cuestionario_existente.escalones else []
            puntaje_total = json.loads(cuestionario_existente.puntaje_total) if cuestionario_existente.puntaje_total else []
            grado_dependencia = json.loads(cuestionario_existente.grado_dependencia) if cuestionario_existente.grado_dependencia else []
            
            # Crear sesiones para la tabla
            for i in range(len(comer)):
                sesiones.append({
                    'sesion': i + 1,
                    'fecha': cuestionario_existente.fecha_creacion.strftime('%d/%m/%Y'),
                    'comer': comer[i] if i < len(comer) else "-",
                    'lavarse': lavarse[i] if i < len(lavarse) else "-",
                    'vestirse': vestirse[i] if i < len(vestirse) else "-",
                    'arreglarse': arreglarse[i] if i < len(arreglarse) else "-",
                    'deposiciones': deposiciones[i] if i < len(deposiciones) else "-",
                    'miccion': miccion[i] if i < len(miccion) else "-",
                    'usar_retrete': usar_retrete[i] if i < len(usar_retrete) else "-",
                    'trasladarse': trasladarse[i] if i < len(trasladarse) else "-",
                    'deambular': deambular[i] if i < len(deambular) else "-",
                    'escalones': escalones[i] if i < len(escalones) else "-",
                    'puntaje_total': puntaje_total[i] if i < len(puntaje_total) else "-",
                    'grado_dependencia': grado_dependencia[i] if i < len(grado_dependencia) else "-"
                })

    return render(request, "CuestionarioBarthel.html", {
        "pacientes": pacientes,
        "clinicos": clinicos,
        "paciente": paciente,
        "cuestionario_existente": cuestionario_existente,
        "clinico_actual": clinico,
        "sesiones": sesiones
    })


def renderizar_CuestionarioENA(request):
    return render(request,"CuestionarioENA.html")

def renderizar_cuestionarioScrening(request):
    return render(request,"CuestionarioScrenning.html")