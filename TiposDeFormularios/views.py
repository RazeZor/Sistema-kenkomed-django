import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from Login.models import (
    CuestionarioScrenning, formularioClinico, Paciente, CuestionarioPSFS,
    Groc, Clinico, CuestionarioEQ_5D, CuestionarioBarthel
)
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime


class BaseEvaluacionHandler: # utilizo esta clase para reutilizar funciones en el codigo
    """Clase base para manejar evaluaciones comunes"""
    
    def __init__(self, request):
        self.request = request
        self.paciente = None
        self.clinico = None
    
    def validar_sesion(self, requiere_admin=False):
        """Valida la sesion del clinico"""
        if 'nombre_clinico' not in self.request.session:
            messages.error(self.request, 'Debe haber un inicio de sesion para acceder a esta pagina.')
            return False
        
        rut_clinico = self.request.session.get('rut_clinico')
        if not rut_clinico:
            messages.error(self.request, 'Debe haber un inicio de sesión para estar aquí...')
            return False
        
        if requiere_admin and not self.request.session.get('es_admin', False):
            messages.error(self.request, 'Se requieren permisos de administrador.')
            return False
        
        try:
            self.clinico = Clinico.objects.get(rut=rut_clinico)
        except Clinico.DoesNotExist:
            messages.error(self.request, 'El clínico no está en el sistema, intenta nuevamente...')
            return False
        
        return True
    
    def obtener_paciente(self):
        """Obtiene el paciente del RUT en GET o POST"""
        rut = self.request.GET.get('rut', '') or self.request.POST.get('rut', '')
        if not rut:
            return None
        
        try:
            self.paciente = Paciente.objects.get(rut=rut)
            return self.paciente
        except Paciente.DoesNotExist:
            messages.error(self.request, 'Paciente no encontrado.')
            return None
    
    def redirect_to_login(self):
        """Redirección común al login"""
        return redirect('login')


def RenderizarGROC(request):
    """Vista refactorizada para GROC"""
    handler = BaseEvaluacionHandler(request)
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    # Verificar evaluación existente
    evaluacion_existente = Groc.objects.filter(paciente=paciente).exists()
    puntajes = []
    NotaGroc = "el Paciente No tiene Notas"
    
    if evaluacion_existente:
        groc_obj = Groc.objects.get(paciente=paciente)
        puntajes = groc_obj.puntajeGroc
        NotaGroc = groc_obj.NotaGroc
    
    if request.method == 'POST':
        return _procesar_groc_post(request, paciente, evaluacion_existente)
    
    return render(request, 'GROC.html', {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluacion_existente': evaluacion_existente,
        'puntajes': puntajes,
        'NotaGroc': NotaGroc
    })


def _procesar_groc_post(request, paciente, evaluacion_existente):
    """Procesa las acciones POST para GROC"""
    fecha_creacion = datetime.now().date()
    puntajeGroc = request.POST.get('puntajeGroc')
    NotaGroc = request.POST.get('nota_adicional')
    action = request.POST.get('action', '')
    
    if not puntajeGroc and action != 'GuardarNota':
        messages.error(request, "El puntaje es obligatorio.")
        return HttpResponseRedirect(request.get_full_path())
    
    try:
        if action == 'guardar':
            Groc.objects.create(
                paciente=paciente,
                fecha_creacion=fecha_creacion,
                NotaGroc=NotaGroc,
                puntajeGroc=[{'puntaje': int(puntajeGroc)}]
            )
            messages.success(request, "Evaluación registrada correctamente.")
            
        elif action == 'actualizar':
            evaluacion = get_object_or_404(Groc, paciente=paciente)
            if isinstance(evaluacion.puntajeGroc, list):
                evaluacion.puntajeGroc.append({'puntaje': int(puntajeGroc)})
            else:
                evaluacion.puntajeGroc = [{'puntaje': int(puntajeGroc)}]
            evaluacion.save()
            messages.success(request, "Evaluación actualizada correctamente.")
            
        elif action == 'GuardarNota':
            evaluacion = get_object_or_404(Groc, paciente=paciente)
            evaluacion.NotaGroc = NotaGroc
            evaluacion.save()
            messages.success(request, "Nota actualizada correctamente.")
            
    except ValueError:
        messages.error(request, "Error en el formato de los datos.")
    except Exception as e:
        messages.error(request, f"Error al procesar la evaluación: {str(e)}")
    
    return HttpResponseRedirect(request.get_full_path())


def gestionar_psfs(request):
    """Vista refactorizada para PSFS"""
    handler = BaseEvaluacionHandler(request)
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    evaluacion_existente = CuestionarioPSFS.objects.filter(paciente=paciente).exists()
    
    if request.method == 'POST':
        return _procesar_psfs_post(request, paciente)
    
    # Preparar datos para renderizado
    cuestionario = CuestionarioPSFS.objects.filter(paciente=paciente).first()
    sesiones = _obtener_sesiones_psfs(cuestionario) if cuestionario else []
    actividades = _obtener_actividades_paciente(paciente)
    nota = cuestionario.NotaCuestionarioPSFS if cuestionario else None
    
    return render(request, 'CuestionarioPSFS.html', {
        'rut': paciente.rut,
        'actividad1': actividades[0],
        'actividad2': actividades[1],
        'actividad3': actividades[2],
        'sesiones_existentes': evaluacion_existente,
        'sesiones': sesiones,
        'evaluacion_existente': evaluacion_existente,
        'nota': nota
    })


def _procesar_psfs_post(request, paciente):
    """Procesa las acciones POST para PSFS"""
    action = request.POST.get('action', '')
    
    puntajes = {
        'actividad_1': request.POST.getlist('rango1'),
        'actividad_2': request.POST.getlist('rango2'),
        'actividad_3': request.POST.getlist('rango3'),
        'total': request.POST.getlist('total_score')
    }
    notaPSFS = request.POST.get('notes')
    
    try:
        if action == 'guardar':
            CuestionarioPSFS.objects.create(
                paciente=paciente,
                fecha_creacion=datetime.now().date(),
                puntaje_actividad_1=json.dumps(puntajes['actividad_1']),
                puntaje_actividad_2=json.dumps(puntajes['actividad_2']),
                puntaje_actividad_3=json.dumps(puntajes['actividad_3']),
                puntajeTotal=json.dumps(puntajes['total']),
            )
            messages.success(request, "Cuestionario guardado correctamente.")
            
        elif action == 'actualizar':
            cuestionario = get_object_or_404(CuestionarioPSFS, paciente=paciente)
            _actualizar_puntajes_psfs(cuestionario, puntajes)
            messages.success(request, "Cuestionario actualizado correctamente.")
        
        if notaPSFS:
            _actualizar_nota_psfs(paciente, notaPSFS)
            messages.success(request, "Nota actualizada correctamente.")
            
    except Exception as e:
        messages.error(request, f"Error al procesar PSFS: {str(e)}")
    
    return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")


def _obtener_sesiones_psfs(cuestionario):
    """Obtiene las sesiones formateadas para PSFS"""
    if not cuestionario:
        return []
    
    puntajes = {
        'actividad_1': json.loads(cuestionario.puntaje_actividad_1 or '[]'),
        'actividad_2': json.loads(cuestionario.puntaje_actividad_2 or '[]'),
        'actividad_3': json.loads(cuestionario.puntaje_actividad_3 or '[]'),
        'total': json.loads(cuestionario.puntajeTotal or '[]')
    }
    
    sesiones = []
    max_length = max(len(p) for p in puntajes.values())
    
    for i in range(max_length):
        sesiones.append({
            "sesion": i + 1,
            "actividad_1": puntajes['actividad_1'][i] if i < len(puntajes['actividad_1']) else "-",
            "actividad_2": puntajes['actividad_2'][i] if i < len(puntajes['actividad_2']) else "-",
            "actividad_3": puntajes['actividad_3'][i] if i < len(puntajes['actividad_3']) else "-",
            "total": puntajes['total'][i] if i < len(puntajes['total']) else "-",
        })
    
    return sesiones


def _obtener_actividades_paciente(paciente):
    """Obtiene las actividades afectadas del paciente"""
    formularios = formularioClinico.objects.filter(paciente=paciente)
    
    if formularios.exists():
        formulario = formularios.first()
        actividades = json.loads(formulario.actividades_afectadas)
        return [
            actividades[0] if len(actividades) > 0 else '',
            actividades[1] if len(actividades) > 1 else '',
            actividades[2] if len(actividades) > 2 else ''
        ]
    
    return ['', '', '']


def _actualizar_puntajes_psfs(cuestionario, nuevos_puntajes):
    """Actualiza los puntajes PSFS existentes"""
    campos = {
        'puntaje_actividad_1': 'actividad_1',
        'puntaje_actividad_2': 'actividad_2', 
        'puntaje_actividad_3': 'actividad_3',
        'puntajeTotal': 'total'
    }
    
    for campo_db, campo_form in campos.items():
        puntajes_actuales = json.loads(getattr(cuestionario, campo_db) or '[]')
        puntajes_actuales.extend(nuevos_puntajes[campo_form])
        setattr(cuestionario, campo_db, json.dumps(puntajes_actuales))
    
    cuestionario.save()


def _actualizar_nota_psfs(paciente, nota):
    """Actualiza la nota PSFS"""
    cuestionario = get_object_or_404(CuestionarioPSFS, paciente=paciente)
    cuestionario.NotaCuestionarioPSFS = nota
    cuestionario.save()


def RenderizarEQ_5D(request):
    """Vista refactorizada para EQ-5D"""
    handler = BaseEvaluacionHandler(request)
    
    if not handler.validar_sesion():
        return handler.redirect_to_login()
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    sesiones_existentes = CuestionarioEQ_5D.objects.filter(paciente=paciente).exists()
    
    if request.method == 'POST':
        return _procesar_eq5d_post(request, paciente, handler.clinico)
    
    puntajes_por_sesion = _obtener_puntajes_eq5d(paciente)
    
    return render(request, 'CuestionarioEQ-5D.html', {
        'rut': paciente.rut,
        'puntajes_por_sesion': puntajes_por_sesion,
        'paciente': paciente,
        'sesiones_existentes': sesiones_existentes
    })


def _procesar_eq5d_post(request, paciente, clinico):
    """Procesa las acciones POST para EQ-5D"""
    action = request.POST.get('action')
    
    try:
        if action == 'actualizar':
            cuestionario, created = CuestionarioEQ_5D.objects.get_or_create(paciente=paciente)
            _actualizar_eq5d(request, cuestionario)
            
        elif action == 'guardar':
            _crear_eq5d(request, paciente, clinico)
        
        messages.success(request, f'El cuestionario se ha {"guardado" if action == "guardar" else "actualizado"} correctamente.')
        
    except Exception as e:
        messages.error(request, f'Error al procesar el cuestionario: {str(e)}')
    
    return HttpResponseRedirect(request.get_full_path())


def _actualizar_eq5d(request, cuestionario):
    """Actualiza un cuestionario EQ-5D existente"""
    campos_puntajes = [
        'puntaje_movilidad', 'puntaje_cuidado_personal', 'puntaje_actividades_cotidianas',
        'puntaje_dolor_malestar', 'puntaje_ansiedad_depresion', 'vas_score'
    ]
    
    for campo in campos_puntajes:
        valor = request.POST.get(campo.replace('puntaje_', '') if campo != 'vas_score' else 'vasScore')
        valores_actuales = getattr(cuestionario, campo)
        valores_actuales.append(valor)
        setattr(cuestionario, campo, valores_actuales)
    
    cuestionario.save()


def _crear_eq5d(request, paciente, clinico):
    """Crea un nuevo cuestionario EQ-5D"""
    campos_lista = ['movilidad', 'cuidadoPersonal', 'actividadesCotidianas', 'dolorMalestar', 'ansiedadDepresion']
    campos_puntajes = ['puntaje_movilidad', 'puntaje_cuidado_personal', 'puntaje_actividades_cotidianas', 
                      'puntaje_dolor_malestar', 'puntaje_ansiedad_depresion', 'vasScore']
    
    datos = {}
    for campo in campos_lista:
        datos[campo] = request.POST.getlist(campo)
    
    for campo in campos_puntajes:
        datos[campo] = request.POST.getlist(campo, None)
    
    CuestionarioEQ_5D.objects.create(
        paciente=paciente,
        clinico=clinico,
        movilidad=datos['movilidad'],
        cuidado_personal=datos['cuidadoPersonal'],
        actividades_cotidianas=datos['actividadesCotidianas'],
        dolor_malestar=datos['dolorMalestar'],
        ansiedad_depresion=datos['ansiedadDepresion'],
        puntaje_movilidad=datos['puntaje_movilidad'],
        puntaje_cuidado_personal=datos['puntaje_cuidado_personal'],
        puntaje_actividades_cotidianas=datos['puntaje_actividades_cotidianas'],
        puntaje_dolor_malestar=datos['puntaje_dolor_malestar'],
        puntaje_ansiedad_depresion=datos['puntaje_ansiedad_depresion'],
        vas_score=datos['vasScore']
    )


def _obtener_puntajes_eq5d(paciente):
    """Obtiene los puntajes formateados para EQ-5D"""
    historial_evaluaciones = CuestionarioEQ_5D.objects.filter(paciente=paciente)
    
    if not historial_evaluaciones.exists():
        return []
    
    puntajes_por_sesion = []
    max_length = max((len(evaluacion.vas_score) for evaluacion in historial_evaluaciones), default=0)
    
    for i in range(max_length):
        for evaluacion in historial_evaluaciones:
            if i < len(evaluacion.vas_score):
                puntajes_por_sesion.append({
                    'sesion': f'{len(puntajes_por_sesion) // len(historial_evaluaciones) + 1}',
                    'vas_score': evaluacion.vas_score[i],
                    'movilidad': evaluacion.puntaje_movilidad[i],
                    'cuidado_personal': evaluacion.puntaje_cuidado_personal[i],
                    'actividades_cotidianas': evaluacion.puntaje_actividades_cotidianas[i],
                    'dolor_malestar': evaluacion.puntaje_dolor_malestar[i],
                    'ansiedad_depresion': evaluacion.puntaje_ansiedad_depresion[i]
                })
    
    return puntajes_por_sesion


def renderizar_CuestionarioBarthel(request):
    """Vista refactorizada para Cuestionario Barthel"""
    handler = BaseEvaluacionHandler(request)
    
    if not handler.validar_sesion():
        return handler.redirect_to_login()
    
    paciente = handler.obtener_paciente()
    
    if request.method == "POST":
        return _procesar_barthel_post(request, paciente, handler.clinico)
    
    # Preparar datos para renderizado
    pacientes = Paciente.objects.all()
    clinicos = Clinico.objects.all()
    cuestionario_existente = None
    sesiones = []
    
    if paciente:
        cuestionario_existente = CuestionarioBarthel.objects.filter(paciente=paciente).first()
        if cuestionario_existente:
            sesiones = _obtener_sesiones_barthel(cuestionario_existente)
    
    return render(request, "CuestionarioBarthel.html", {
        "pacientes": pacientes,
        "clinicos": clinicos,
        "paciente": paciente,
        "cuestionario_existente": cuestionario_existente,
        "clinico_actual": handler.clinico,
        "sesiones": sesiones
    })


def _procesar_barthel_post(request, paciente, clinico):
    """Procesa las acciones POST para Barthel"""
    if not paciente:
        paciente_rut = request.POST.get("paciente")
        if paciente_rut:
            paciente = get_object_or_404(Paciente, rut=paciente_rut)
        else:
            messages.error(request, "Debe seleccionar un paciente.")
            return redirect('bartel')
    
    action = request.POST.get('action', '')
    notaBarthel = request.POST.get('nota_adicional', '')
    
    try:
        if action in ['guardar', 'actualizar']:
            datos, total, grado = _procesar_datos_barthel(request)
            
            if action == 'guardar':
                _crear_barthel(paciente, clinico, datos, total, grado, notaBarthel)
                messages.success(request, f"Cuestionario Barthel guardado correctamente. Puntaje: {total}, Grado: {grado}")
            
            elif action == 'actualizar':
                _actualizar_barthel(paciente, datos, total, grado)
                messages.success(request, f"Cuestionario Barthel actualizado correctamente. Puntaje: {total}, Grado: {grado}")
        
        elif action == 'GuardarNota':
            cuestionario = get_object_or_404(CuestionarioBarthel, paciente=paciente)
            cuestionario.NotaCuestionarioBarthel = notaBarthel
            cuestionario.save()
            messages.success(request, "Nota actualizada correctamente.")
        
    except Exception as e:
        messages.error(request, f"Error al procesar el cuestionario: {str(e)}")
    
    return redirect(f"{reverse('bartel')}?rut={paciente.rut}")


def _procesar_datos_barthel(request):
    """Procesa y valida los datos del cuestionario Barthel"""
    campos = [
        "comer", "lavarse", "vestirse", "arreglarse",
        "deposiciones", "miccion", "usar_retrete",
        "trasladarse", "deambular", "escalones"
    ]
    
    datos = {}
    for campo in campos:
        valor = request.POST.get(campo)
        if valor is None or valor == "":
            raise ValueError(f"Falta el campo: {campo}")
        
        try:
            datos[campo] = int(valor)
        except ValueError:
            raise ValueError(f"Valor inválido en {campo}")
    
    total = sum(datos.values())
    if datos.get("deambular") == 5 and total > 90:
        total = 90
    
    # Determinar grado de dependencia
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
    
    return datos, total, grado


def _crear_barthel(paciente, clinico, datos, total, grado, nota):
    """Crea un nuevo cuestionario Barthel"""
    CuestionarioBarthel.objects.create(
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
        NotaCuestionarioBarthel=nota
    )


def _actualizar_barthel(paciente, datos, total, grado):
    """Actualiza un cuestionario Barthel existente"""
    cuestionario = get_object_or_404(CuestionarioBarthel, paciente=paciente)
    
    campos = [
        "comer", "lavarse", "vestirse", "arreglarse",
        "deposiciones", "miccion", "usar_retrete",
        "trasladarse", "deambular", "escalones"
    ]
    
    for campo in campos:
        valores_actuales = json.loads(getattr(cuestionario, campo) or '[]')
        valores_actuales.append(datos[campo])
        setattr(cuestionario, campo, json.dumps(valores_actuales))
    
    # Actualizar puntaje total y grado
    puntaje_total_actual = json.loads(cuestionario.puntaje_total or '[]')
    grado_dependencia_actual = json.loads(cuestionario.grado_dependencia or '[]')
    
    puntaje_total_actual.append(total)
    grado_dependencia_actual.append(grado)
    
    cuestionario.puntaje_total = json.dumps(puntaje_total_actual)
    cuestionario.grado_dependencia = json.dumps(grado_dependencia_actual)
    cuestionario.save()


def _obtener_sesiones_barthel(cuestionario):
    """Obtiene las sesiones formateadas para Barthel"""
    campos = [
        'comer', 'lavarse', 'vestirse', 'arreglarse', 'deposiciones',
        'miccion', 'usar_retrete', 'trasladarse', 'deambular', 'escalones'
    ]
    
    datos_sesiones = {}
    for campo in campos:
        datos_sesiones[campo] = json.loads(getattr(cuestionario, campo) or '[]')
    
    puntaje_total = json.loads(cuestionario.puntaje_total or '[]')
    grado_dependencia = json.loads(cuestionario.grado_dependencia or '[]')
    
    sesiones = []
    max_length = max(len(datos_sesiones[campo]) for campo in campos)
    
    for i in range(max_length):
        sesion = {
            'sesion': i + 1,
            'fecha': cuestionario.fecha_creacion.strftime('%d/%m/%Y'),
            'puntaje_total': puntaje_total[i] if i < len(puntaje_total) else "-",
            'grado_dependencia': grado_dependencia[i] if i < len(grado_dependencia) else "-"
        }
        
        for campo in campos:
            sesion[campo] = datos_sesiones[campo][i] if i < len(datos_sesiones[campo]) else "-"
        
        sesiones.append(sesion)
    
    return sesiones


def renderizar_cuestionarioScrening(request):
    """Vista corregida para Cuestionario Screening"""
    handler = BaseEvaluacionHandler(request)
    
    if not handler.validar_sesion(requiere_admin=True):
        return handler.redirect_to_login()
    
    paciente = handler.obtener_paciente()
    if not paciente:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('panel')
    
    # Verificar si ya existe una evaluación
    evaluacion_existente = CuestionarioScrenning.objects.filter(paciente=paciente).exists()
    cuestionario_actual = None

    sesiones = CuestionarioScrenning.objects.filter(paciente=paciente)
    
    if evaluacion_existente:
        cuestionario_actual = CuestionarioScrenning.objects.get(paciente=paciente)
    
    if request.method == "POST":
        return _procesar_screening_post(request, paciente, handler.clinico)
    
    return render(request, "CuestionarioScrenning.html", {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluacion_existente': evaluacion_existente,
        'cuestionario': cuestionario_actual,
        'sesiones': sesiones
    })


def _procesar_screening_post(request, paciente, clinico):
    """Procesa las acciones POST para Screening"""
    try:
        intensidad_dolor = request.POST.get('IntensidadDolor')
        respuestas_tabla = request.POST.getlist('preguntas1')  # Cambiar a getlist para multiples respuestas
        necesidad_apoyo = request.POST.get('nesesidadDeApoyo')
        action = request.POST.get('action', 'guardar')
        
        # Validaciones básicas
        if not intensidad_dolor:
            messages.error(request, "La intensidad del dolor es obligatoria.")
            return redirect(f"{reverse('cuestionario_screening')}?rut={paciente.rut}")
        
        if action == 'guardar':
            # Verificar si ya existe (OneToOneField)
            if CuestionarioScrenning.objects.filter(paciente=paciente).exists():
                messages.error(request, "Ya existe una evaluación para este paciente. Use actualizar.")
                return redirect(f"{reverse('cuestionario_screening')}?rut={paciente.rut}")
            
            CuestionarioScrenning.objects.create(
                paciente=paciente,
                clinico=clinico,
                IntensidadDolor=intensidad_dolor,
                RespuestasTabla1=respuestas_tabla,  # Se guarda como JSONField
                nesesidadDeApoyo=necesidad_apoyo,
            )
            messages.success(request, "Cuestionario de screening guardado correctamente.")
        
        elif action == 'actualizar':
            cuestionario = get_object_or_404(CuestionarioScrenning, paciente=paciente)
            cuestionario.IntensidadDolor = intensidad_dolor
            cuestionario.RespuestasTabla1 = respuestas_tabla
            cuestionario.nesesidadDeApoyo = necesidad_apoyo
            cuestionario.save()
            messages.success(request, "Cuestionario de screening actualizado correctamente.")
        
        return redirect(f"{reverse('cuestionario_screening')}?rut={paciente.rut}")
        
    except Exception as e:
        messages.error(request, f"Error al procesar el cuestionario de screening: {str(e)}")
        return redirect('panel')


def renderizar_CuestionarioENA(request):
    return render(request, "CuestionarioENA.html")