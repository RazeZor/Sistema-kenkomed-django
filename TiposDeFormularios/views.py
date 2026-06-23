import json
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from Login.models import (
    CuestionarioScrenning, formularioClinico, Paciente, CuestionarioPSFS,
    Groc, Clinico, CuestionarioEQ_5D, CuestionarioBarthel
)
from Login.models import CuestionarioEvaluacionENA
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from datetime import datetime
from clinicas.utils import obtener_paciente_por_rut
from Login.auditoria import auditar_cuestionario_consulta, auditar_cuestionario_edicion


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
        """Obtiene el paciente del RUT en GET o POST, respetando la clínica de sesión."""
        rut = self.request.GET.get('rut', '') or self.request.POST.get('rut', '')
        if not rut:
            return None

        self.paciente = obtener_paciente_por_rut(self.request, rut)
        if not self.paciente:
            messages.error(self.request, 'Paciente no encontrado o no tienes permiso de acceso.')
        return self.paciente
    
    def redirect_to_login(self):
        """Redirección común al login"""
        return redirect('login')

    def auditar_consulta(self, nombre_cuestionario):
        if self.paciente:
            auditar_cuestionario_consulta(self.request, self.paciente, nombre_cuestionario)

    def auditar_edicion(self, nombre_cuestionario, subaccion=''):
        if self.paciente:
            auditar_cuestionario_edicion(self.request, self.paciente, nombre_cuestionario, subaccion)


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

    auditar_cuestionario_consulta(request, paciente, 'GROC')
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
            auditar_cuestionario_edicion(request, paciente, 'GROC', 'nueva evaluación')
            messages.success(request, "Evaluación registrada correctamente.")
            
        elif action == 'actualizar':
            evaluacion = get_object_or_404(Groc, paciente=paciente)
            if isinstance(evaluacion.puntajeGroc, list):
                evaluacion.puntajeGroc.append({'puntaje': int(puntajeGroc)})
            else:
                evaluacion.puntajeGroc = [{'puntaje': int(puntajeGroc)}]
            evaluacion.save()
            auditar_cuestionario_edicion(request, paciente, 'GROC', 'nueva sesión')
            messages.success(request, "Evaluación actualizada correctamente.")
            
        elif action == 'GuardarNota':
            evaluacion = get_object_or_404(Groc, paciente=paciente)
            evaluacion.NotaGroc = NotaGroc
            evaluacion.save()
            auditar_cuestionario_edicion(request, paciente, 'GROC', 'nota clínica')
            messages.success(request, "Nota actualizada correctamente.")
            
    except ValueError:
        messages.error(request, "Error en el formato de los datos.")
    except Exception as e:
        messages.error(request, f"Error al procesar la evaluación: {str(e)}")
    
    return HttpResponseRedirect(request.get_full_path())


def gestionar_psfs(request):
    """Vista para manejar el cuestionario PSFS con actividades manuales"""
    handler = BaseEvaluacionHandler(request)
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    cuestionario = CuestionarioPSFS.objects.filter(paciente=paciente).first()
    if cuestionario:
        from TiposDeFormularios.psfs_utils import repair_psfs_stored_totals
        repair_psfs_stored_totals(cuestionario)
    
    if request.method == 'POST':
        return _procesar_psfs_post(request, paciente, cuestionario)
    
    # Preparar datos para renderizado
    sesiones = _obtener_sesiones_psfs(cuestionario) if cuestionario else []
    ultima = sesiones[-1] if sesiones else None

    handler.auditar_consulta('PSFS')
    return render(request, 'CuestionarioPSFS.html', {
        'rut': paciente.rut,
        'actividad1': cuestionario.actividad_1 if cuestionario else '',
        'actividad2': cuestionario.actividad_2 if cuestionario else '',
        'actividad3': cuestionario.actividad_3 if cuestionario else '',
        'sesiones': sesiones,
        'evaluacion_existente': cuestionario is not None,
        'nota': cuestionario.NotaCuestionarioPSFS if cuestionario else None,
        'rango1': ultima['actividad_1'] if ultima else 5,
        'rango2': ultima['actividad_2'] if ultima else 5,
        'rango3': ultima['actividad_3'] if ultima else 5,
    })


def _procesar_psfs_post(request, paciente, cuestionario):
    """Procesa las acciones POST para PSFS con actividades manuales."""
    from TiposDeFormularios.psfs_utils import (
        append_psfs_scores,
        initial_psfs_scores,
        replace_last_psfs_session,
        scores_from_post,
    )

    action = request.POST.get('action', '')

    actividad_1 = request.POST.get('actividad_1', '').strip()
    actividad_2 = request.POST.get('actividad_2', '').strip()
    actividad_3 = request.POST.get('actividad_3', '').strip()

    if action == 'guardar' and not all([actividad_1, actividad_2, actividad_3]):
        messages.error(request, 'Debe ingresar las tres actividades para continuar.')
        return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")

    if action == 'GuardarNota' or 'notes' in request.POST:
        notaPSFS = request.POST.get('notes', '').strip()
        if not notaPSFS and 'nota_adicional' in request.POST:
            notaPSFS = request.POST.get('nota_adicional', '').strip()

        if not notaPSFS:
            messages.error(request, 'No se proporcionó ninguna nota para guardar.')
        elif _actualizar_nota_psfs(paciente, notaPSFS):
            auditar_cuestionario_edicion(request, paciente, 'PSFS', 'nota clínica')
            messages.success(request, 'Nota guardada correctamente.')
        else:
            messages.error(request, 'Error al guardar la nota. Asegúrese de que el cuestionario existe.')
        return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")

    puntajes = scores_from_post(request.POST)
    notaPSFS = request.POST.get('nota_adicional', '')

    if action in ('guardar', 'actualizar') and not any(
        puntajes[k] for k in ('actividad_1', 'actividad_2', 'actividad_3')
    ):
        messages.error(request, 'Debe asignar puntaje a las tres actividades antes de guardar.')
        return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")

    try:
        if action == 'guardar':
            scores = initial_psfs_scores(puntajes)
            CuestionarioPSFS.objects.create(
                paciente=paciente,
                fecha_creacion=datetime.now().date(),
                actividad_1=actividad_1,
                actividad_2=actividad_2,
                actividad_3=actividad_3,
                NotaCuestionarioPSFS=notaPSFS,
                **scores,
            )
            auditar_cuestionario_edicion(request, paciente, 'PSFS', 'nueva evaluación')
            messages.success(request, 'Cuestionario guardado correctamente.')

        elif action == 'actualizar':
            if not cuestionario:
                cuestionario = get_object_or_404(CuestionarioPSFS, paciente=paciente)

            if actividad_1:
                cuestionario.actividad_1 = actividad_1
            if actividad_2:
                cuestionario.actividad_2 = actividad_2
            if actividad_3:
                cuestionario.actividad_3 = actividad_3

            nueva_sesion = request.POST.get('nueva_sesion') in ('1', 'on', 'true')
            if nueva_sesion:
                append_psfs_scores(cuestionario, puntajes)
                auditar_cuestionario_edicion(request, paciente, 'PSFS', 'nueva sesión de seguimiento')
                messages.success(request, 'Nueva sesión de seguimiento registrada.')
            else:
                replace_last_psfs_session(cuestionario, puntajes)
                auditar_cuestionario_edicion(request, paciente, 'PSFS', 'actualización de sesión')
                messages.success(request, 'Evaluación actualizada correctamente.')

            if 'nota_adicional' in request.POST:
                cuestionario.NotaCuestionarioPSFS = notaPSFS

            cuestionario.save()

    except Exception as e:
        messages.error(request, f'Error al procesar el cuestionario: {str(e)}')

    return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")


def _actualizar_puntajes_psfs(cuestionario, nuevos_puntajes):
    """Compatibilidad: delega en append_psfs_scores."""
    from TiposDeFormularios.psfs_utils import append_psfs_scores
    append_psfs_scores(cuestionario, nuevos_puntajes)
    cuestionario.save()


def _obtener_sesiones_psfs(cuestionario):
    """Obtiene las sesiones formateadas para PSFS."""
    from TiposDeFormularios.psfs_utils import build_psfs_sessions
    return build_psfs_sessions(cuestionario)


def _actualizar_nota_psfs(paciente, nota):
    """Actualiza la nota PSFS"""
    try:
        cuestionario = CuestionarioPSFS.objects.filter(paciente=paciente).first()
        if not cuestionario:
            return False
            
        cuestionario.NotaCuestionarioPSFS = nota
        cuestionario.save()
        return True
    except Exception as e:
        print(f"Error al actualizar la nota PSFS: {e}")
        return False


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

    handler.auditar_consulta('EQ-5D')
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

        if action in ('guardar', 'actualizar'):
            auditar_cuestionario_edicion(
                request, paciente, 'EQ-5D',
                'nueva evaluación' if action == 'guardar' else 'nueva sesión',
            )
        
        messages.success(request, f'El cuestionario se ha {"guardado" if action == "guardar" else "actualizado"} correctamente.')
        
    except Exception as e:
        messages.error(request, f'Error al procesar el cuestionario: {str(e)}')
    
    return HttpResponseRedirect(request.get_full_path())


def _actualizar_eq5d(request, cuestionario):
    """Actualiza un cuestionario EQ-5D existente"""
    # Get all the scores from the form
    puntajes = {
        'puntaje_movilidad': request.POST.get('puntaje_movilidad'),
        'puntaje_cuidado_personal': request.POST.get('puntaje_cuidado_personal'),
        'puntaje_actividades_cotidianas': request.POST.get('puntaje_actividades_cotidianas'),
        'puntaje_dolor_malestar': request.POST.get('puntaje_dolor_malestar'),
        'puntaje_ansiedad_depresion': request.POST.get('puntaje_ansiedad_depresion'),
        'vas_score': request.POST.get('vasScore')
    }
    
    # Update each field, initializing the list if it doesn't exist
    for campo, valor in puntajes.items():
        if valor is not None:
            # Get current values or initialize empty list
            valores_actuales = getattr(cuestionario, campo, []) or []
            # Append new value as integer
            try:
                valores_actuales.append(int(valor))
                # Save back to the model
                setattr(cuestionario, campo, valores_actuales)
            except (ValueError, TypeError) as e:
                print(f"Error al convertir el valor para {campo}: {e}")
    
    cuestionario.save()


def _crear_eq5d(request, paciente, clinico):
    """Crea un nuevo cuestionario EQ-5D"""
    # Get all the data from the form
    datos = {
        'movilidad': [request.POST.get('movilidad')],
        'cuidado_personal': [request.POST.get('cuidadoPersonal')],
        'actividades_cotidianas': [request.POST.get('actividadesCotidianas')],
        'dolor_malestar': [request.POST.get('dolorMalestar')],
        'ansiedad_depresion': [request.POST.get('ansiedadDepresion')],
        'puntaje_movilidad': [int(request.POST.get('puntaje_movilidad', 0))],
        'puntaje_cuidado_personal': [int(request.POST.get('puntaje_cuidado_personal', 0))],
        'puntaje_actividades_cotidianas': [int(request.POST.get('puntaje_actividades_cotidianas', 0))],
        'puntaje_dolor_malestar': [int(request.POST.get('puntaje_dolor_malestar', 0))],
        'puntaje_ansiedad_depresion': [int(request.POST.get('puntaje_ansiedad_depresion', 0))],
        'vas_score': [int(request.POST.get('vasScore', 0))]
    }
    
    # Create the questionnaire
    cuestionario = CuestionarioEQ_5D.objects.create(
        paciente=paciente,
        clinico=clinico,
        **datos
    )
    return cuestionario


def _obtener_puntajes_eq5d(paciente):
    """Obtiene los puntajes formateados para EQ-5D"""
    try:
        evaluacion = CuestionarioEQ_5D.objects.get(paciente=paciente)
    except CuestionarioEQ_5D.DoesNotExist:
        return []
    
    puntajes_por_sesion = []
    
    # Get the maximum length of any score list
    max_length = max(
        len(evaluacion.vas_score or []),
        len(evaluacion.puntaje_movilidad or []),
        len(evaluacion.puntaje_cuidado_personal or []),
        len(evaluacion.puntaje_actividades_cotidianas or []),
        len(evaluacion.puntaje_dolor_malestar or []),
        len(evaluacion.puntaje_ansiedad_depresion or [])
    )
    
    if max_length == 0:
        return []
    
    # For each session
    for i in range(max_length):
        try:
            puntaje = {
                'sesion': i + 1,
                'fecha': f"Sesión {i + 1}",
                'vas_score': evaluacion.vas_score[i] if evaluacion.vas_score and i < len(evaluacion.vas_score) else None,
                'movilidad': evaluacion.puntaje_movilidad[i] if evaluacion.puntaje_movilidad and i < len(evaluacion.puntaje_movilidad) else None,
                'cuidado_personal': evaluacion.puntaje_cuidado_personal[i] if evaluacion.puntaje_cuidado_personal and i < len(evaluacion.puntaje_cuidado_personal) else None,
                'actividades_cotidianas': evaluacion.puntaje_actividades_cotidianas[i] if evaluacion.puntaje_actividades_cotidianas and i < len(evaluacion.puntaje_actividades_cotidianas) else None,
                'dolor_malestar': evaluacion.puntaje_dolor_malestar[i] if evaluacion.puntaje_dolor_malestar and i < len(evaluacion.puntaje_dolor_malestar) else None,
                'ansiedad_depresion': evaluacion.puntaje_ansiedad_depresion[i] if evaluacion.puntaje_ansiedad_depresion and i < len(evaluacion.puntaje_ansiedad_depresion) else None
            }
            puntajes_por_sesion.append(puntaje)
        except (IndexError, TypeError) as e:
            print(f"Error al procesar los datos de la evaluación: {e}")
            continue
    
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

    handler.auditar_consulta('Barthel')
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
                auditar_cuestionario_edicion(request, paciente, 'Barthel', 'nueva evaluación')
                messages.success(request, f"Cuestionario Barthel guardado correctamente. Puntaje: {total}, Grado: {grado}")
            
            elif action == 'actualizar':
                _actualizar_barthel(paciente, datos, total, grado)
                auditar_cuestionario_edicion(request, paciente, 'Barthel', 'nueva sesión')
                messages.success(request, f"Cuestionario Barthel actualizado correctamente. Puntaje: {total}, Grado: {grado}")
        
        elif action == 'GuardarNota':
            cuestionario = get_object_or_404(CuestionarioBarthel, paciente=paciente)
            cuestionario.NotaCuestionarioBarthel = notaBarthel
            cuestionario.save()
            auditar_cuestionario_edicion(request, paciente, 'Barthel', 'nota clínica')
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

    if not handler.validar_sesion(requiere_admin=False):
        return handler.redirect_to_login()

    paciente = handler.obtener_paciente()
    if not paciente:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('panel')

    # Verificar si ya existe una evaluación
    evaluacion_existente = CuestionarioScrenning.objects.filter(paciente=paciente).exists()
    cuestionario_actual = None

    if evaluacion_existente:
        cuestionario_actual = CuestionarioScrenning.objects.get(paciente=paciente)

    if request.method == "POST":
        return _procesar_screening_post(request, paciente, handler.clinico)

    # Obtener todas las evaluaciones del paciente

    toda_evaluacion_existente = CuestionarioScrenning.objects.filter(paciente=paciente)
    # Si existe la evaluación actual, generar alerta
    alerta = generar_alerta(cuestionario_actual.Puntaje_Sesion) if cuestionario_actual else None

    handler.auditar_consulta('Screening (Örebro)')
    return render(request, "CuestionarioScrenning.html", {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluacion_existente': evaluacion_existente,
        'cuestionario': cuestionario_actual,
        'alerta': alerta,
        'toda_evaluacion_existente':toda_evaluacion_existente,
    })


def _procesar_screening_post(request, paciente, clinico):
    """Procesa las acciones POST para Screening"""
    try:
        # Obtener datos del formulario
        intensidad_dolor = request.POST.get('IntensidadDolor')
        respuestas_tabla = request.POST.getlist('preguntas1[]')  # Corregido el nombre del campo
        nivel_molestia = request.POST.get('NivelMolestia')
        nota = request.POST.get('nota_adicional', '')
        action = request.POST.get('action', 'guardar')

        # Validaciones básicas
        missing = []

        # Requerimos Intensidad y Nivel de Molestia para guardar o actualizar
        if action in ['guardar', 'actualizar']:
            if not intensidad_dolor:
                missing.append('Intensidad del dolor')
            if not nivel_molestia:
                missing.append('Nivel de molestia')

            # Validar que todas las preguntas funcionales tengan respuesta.
            # En la plantilla hay 8 preguntas funcionales (cada una con un par Sí/No). Ajusta este número si cambias la plantilla.
            EXPECTED_FUNC_QUESTIONS = 8
            if not respuestas_tabla or len(respuestas_tabla) < EXPECTED_FUNC_QUESTIONS:
                missing.append('Todas las preguntas funcionales (marcar Sí o No en cada una)')

            if missing:
                # En lugar de redirigir al panel, renderizamos la misma plantilla con información
                # sobre los campos faltantes y los valores enviados para que el clínico corrija.
                evaluacion_existente = CuestionarioScrenning.objects.filter(paciente=paciente).exists()
                cuestionario_actual = None
                if evaluacion_existente:
                    cuestionario_actual = CuestionarioScrenning.objects.get(paciente=paciente)
                toda_evaluacion_existente = CuestionarioScrenning.objects.filter(paciente=paciente)
                alerta = generar_alerta(cuestionario_actual.Puntaje_Sesion) if cuestionario_actual else None

                context = {
                    'rut': paciente.rut,
                    'paciente': paciente,
                    'evaluacion_existente': evaluacion_existente,
                    'cuestionario': cuestionario_actual,
                    'alerta': alerta,
                    'toda_evaluacion_existente': toda_evaluacion_existente,
                    'missing_fields': missing,
                    'posted_intensidad': intensidad_dolor,
                    'posted_nivel': nivel_molestia,
                    'posted_respuestas': respuestas_tabla,
                }

                # Señalamos si faltan respuestas de la sección funcional para resaltarla en la plantilla
                context['missing_checks'] = any('preguntas funcionales' in m.lower() for m in missing)

                return render(request, 'CuestionarioScrenning.html', context)

        # Calcular puntaje
        puntaje_sesion = calcular_puntaje(respuestas_tabla, nivel_molestia)

        if action == 'guardar':
            # Verificar si ya existe (OneToOneField)
            if CuestionarioScrenning.objects.filter(paciente=paciente).exists():
                messages.error(request, "Ya existe una evaluación para este paciente. Use 'Actualizar Evaluación'.")
                return redirect(f"{reverse('cuestionario_screening')}?rut={paciente.rut}")

            # Crear nuevo cuestionario
            CuestionarioScrenning.objects.create(
                paciente=paciente,
                clinico=clinico,
                IntensidadDolor=intensidad_dolor,
                RespuestasTabla1=respuestas_tabla,
                NivelMolestia=nivel_molestia,
                Puntaje_Sesion=puntaje_sesion,
                Nota_CuestionarioScrenning=nota
            )
            auditar_cuestionario_edicion(request, paciente, 'Screening (Örebro)', 'nueva evaluación')
            messages.success(request, "Cuestionario de screening guardado correctamente.")

        elif action == 'actualizar':
            try:
                cuestionario = CuestionarioScrenning.objects.get(paciente=paciente)
                cuestionario.IntensidadDolor = intensidad_dolor
                cuestionario.RespuestasTabla1 = respuestas_tabla
                cuestionario.NivelMolestia = nivel_molestia
                cuestionario.Puntaje_Sesion = puntaje_sesion
                cuestionario.Nota_CuestionarioScrenning = nota
                cuestionario.save()
                auditar_cuestionario_edicion(request, paciente, 'Screening (Örebro)', 'actualización')
                messages.success(request, "Cuestionario de screening actualizado correctamente.")
            except CuestionarioScrenning.DoesNotExist:
                messages.error(request, "No existe una evaluación previa para actualizar.")
                return redirect(f"{reverse('cuestionario_screening')}?rut={paciente.rut}")

        return HttpResponseRedirect(request.get_full_path())

    except Exception as e:
        messages.error(request, f"Error al procesar el cuestionario de screening: {str(e)}")
        return redirect('panel')



def calcular_puntaje(respuestas, nivel_molestia):
    """Calcula el puntaje basado en las respuestas"""
    if not respuestas:
        respuestas = []

    if not nivel_molestia:
        nivel_molestia = ''

    puntaje = 0

    # Contar respuestas afirmativas
    puntaje += respuestas.count('si')

    # Agregar punto por nivel de molestia alto
    if nivel_molestia.lower() in ['moderado', 'mucho', 'extremo']:
        puntaje += 1

    return puntaje


def generar_alerta(puntaje):
    """Genera mensaje de alerta basado en el puntaje"""
    if puntaje <= 3:
        color, mensaje = '#d4edda', 'Riesgo bajo: educar y tranquilizar al paciente.'
        nivel = 'BAJO'
    elif 4 <= puntaje <= 7:
        color, mensaje = '#fff3cd', 'Riesgo medio: evaluar si necesitará ayuda de otro profesional.'
        nivel = 'MEDIO'
    else:
        color, mensaje = '#f8d7da', 'Riesgo alto: se recomienda tratamiento interdisciplinario.'
        nivel = 'ALTO'

    return {
        'html': f'<div style="background-color: {color}; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb; margin: 10px 0;"><strong>Riesgo {nivel}:</strong> {mensaje}</div>',
        'nivel': nivel,
        'puntaje': puntaje,
        'mensaje': mensaje
    }

def renderizar_CuestionarioENA(request):
    handler = BaseEvaluacionHandler(request)

    if not handler.validar_sesion():
        return handler.redirect_to_login()

    paciente = handler.obtener_paciente()
    if not paciente:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('panel')

    # Obtener o crear cuestionario ENA asociado al paciente
    cuestionario = CuestionarioEvaluacionENA.objects.filter(paciente=paciente).first()
    evaluations = cuestionario.estado_por_sesion if cuestionario and cuestionario.estado_por_sesion else []

    if request.method == 'POST':
        action = request.POST.get('action', 'guardar')
        try:
            if action == 'guardar':
                # datos mínimos esperados: level, description, timestamp, session
                level = int(request.POST.get('level'))
                description = request.POST.get('description', '')
                timestamp = request.POST.get('timestamp') or datetime.now().isoformat()
                session_id = request.POST.get('session') or f"S{int(datetime.now().timestamp())}"

                nueva = {
                    'level': level,
                    'description': description,
                    'timestamp': timestamp,
                    'session': session_id
                }

                if not cuestionario:
                    cuestionario = CuestionarioEvaluacionENA.objects.create(
                        paciente=paciente,
                        clinico=handler.clinico,
                        fecha_creacion=datetime.now().date(),
                        estado_por_sesion=[nueva]
                    )
                else:
                    estado = cuestionario.estado_por_sesion or []
                    estado.append(nueva)
                    cuestionario.estado_por_sesion = estado
                    cuestionario.save()

                auditar_cuestionario_edicion(request, paciente, 'ENA', 'nueva evaluación')
                messages.success(request, 'Evaluación guardada correctamente.')

            elif action == 'delete':
                # eliminar por índice
                index = int(request.POST.get('index', -1))
                if cuestionario and 0 <= index < len(cuestionario.estado_por_sesion):
                    estado = cuestionario.estado_por_sesion
                    estado.pop(index)
                    cuestionario.estado_por_sesion = estado
                    cuestionario.save()
                    auditar_cuestionario_edicion(request, paciente, 'ENA', f'eliminó evaluación índice {index}')
                    messages.success(request, 'Evaluación eliminada.')
                else:
                    messages.error(request, 'Índice no válido para eliminar.')

            elif action == 'clear':
                if cuestionario:
                    cuestionario.estado_por_sesion = []
                    cuestionario.save()
                auditar_cuestionario_edicion(request, paciente, 'ENA', 'limpieza de historial')
                messages.success(request, 'Historial limpiado.')

        except Exception as e:
            messages.error(request, f'Error al procesar la petición: {str(e)}')

        return HttpResponseRedirect(request.get_full_path())

    # Render GET: inyectar las evaluaciones (serializadas) en el template
    import json as _json
    evaluations_json = _json.dumps(evaluations)

    handler.auditar_consulta('ENA')
    return render(request, "CuestionarioENA.html", {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluations_json': evaluations_json,
        'evaluations': evaluations,
        'clinico_actual': handler.clinico
    })


# ==================== CUESTIONARIO OSWESTRY (ODI) ====================

def renderizar_cuestionario_oswestry(request):
    """Vista para manejar el cuestionario Oswestry (ODI)"""
    from .models import EvaluacionOswestry
    
    handler = BaseEvaluacionHandler(request)
    
    if not handler.validar_sesion():
        return handler.redirect_to_login()
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    if request.method == 'POST':
        return _procesar_oswestry_post(request, paciente, handler.clinico)
    
    # Obtener evaluaciones existentes
    evaluaciones = EvaluacionOswestry.objects.filter(paciente=paciente).order_by('fecha_evaluacion')
    evaluations_count = evaluaciones.count()
    
    # Preparar datos para el gráfico de evolución
    evaluations_data = []
    for eval in evaluaciones:
        evaluations_data.append({
            'fecha': eval.fecha_evaluacion.strftime('%d/%m/%Y'),
            'porcentaje': eval.get_porcentaje_incapacidad(),
            'puntos': eval.get_total_puntos(),
            'nivel': eval.get_interpretacion()['nivel']
        })
    
    evaluations_json = json.dumps(evaluations_data)

    handler.auditar_consulta('Oswestry (ODI)')
    return render(request, 'CuestionarioOswestry.html', {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluations_json': evaluations_json,
        'evaluations_count': evaluations_count,
        'evaluaciones': evaluaciones
    })


def _procesar_oswestry_post(request, paciente, clinico):
    """Procesa las acciones POST para Oswestry"""
    from .models import EvaluacionOswestry
    
    action = request.POST.get('action', 'guardar')
    
    try:
        # Obtener los valores de las 10 secciones
        secciones = {}
        for i in range(1, 11):
            campo_nombre = f'seccion_{i}'
            # Mapeo de nombres de campos del formulario
            campo_map = {
                'seccion_1': 'seccion_1_intensidad_dolor',
                'seccion_2': 'seccion_2_estar_de_pie',
                'seccion_3': 'seccion_3_cuidados_personales',
                'seccion_4': 'seccion_4_dormir',
                'seccion_5': 'seccion_5_levantar_peso',
                'seccion_6': 'seccion_6_actividad_sexual',
                'seccion_7': 'seccion_7_andar',
                'seccion_8': 'seccion_8_vida_social',
                'seccion_9': 'seccion_9_estar_sentado',
                'seccion_10': 'seccion_10_viajar'
            }
            
            valor = request.POST.get(campo_map[campo_nombre])
            if valor is None or valor == '':
                messages.error(request, f'Debe completar todas las secciones del cuestionario. Falta la sección {i}.')
                return redirect(f"{reverse('oswestry')}?rut={paciente.rut}")
            
            try:
                secciones[campo_map[campo_nombre]] = int(valor)
            except ValueError:
                messages.error(request, f'Valor inválido en la sección {i}.')
                return redirect(f"{reverse('oswestry')}?rut={paciente.rut}")
        
        # Obtener notas clínicas opcionales
        notas_clinicas = request.POST.get('notas_clinicas', '')
        
        # Crear nueva evaluación
        evaluacion = EvaluacionOswestry.objects.create(
            paciente=paciente,
            clinico=clinico,
            notas_clinicas=notas_clinicas,
            **secciones
        )
        
        # Obtener interpretación para el mensaje
        interpretacion = evaluacion.get_interpretacion()
        porcentaje = evaluacion.get_porcentaje_incapacidad()

        auditar_cuestionario_edicion(request, paciente, 'Oswestry (ODI)', 'nueva evaluación')
        
        messages.success(
            request, 
            f'Evaluación Oswestry guardada correctamente. '
            f'Resultado: {porcentaje}% - {interpretacion["nivel"]}'
        )
        
    except Exception as e:
        messages.error(request, f'Error al procesar la evaluación: {str(e)}')
    
    return redirect(f"{reverse('oswestry')}?rut={paciente.rut}")


# ==================== ESCALA FUNCIONAL EXTREMIDAD INFERIOR (LEFS) ====================

def renderizar_cuestionario_lefs(request):
    """Vista para manejar la Escala Funcional de la Extremidad Inferior (LEFS)"""
    from .models import EvaluacionLEFS
    
    handler = BaseEvaluacionHandler(request)
    
    if not handler.validar_sesion():
        return handler.redirect_to_login()
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    if request.method == 'POST':
        return _procesar_lefs_post(request, paciente, handler.clinico)
    
    # Obtener evaluaciones existentes
    evaluaciones = EvaluacionLEFS.objects.filter(paciente=paciente).order_by('fecha_evaluacion')
    evaluations_count = evaluaciones.count()
    
    # Preparar datos para el gráfico de evolución
    evaluations_data = []
    for eval in evaluaciones:
        evaluations_data.append({
            'fecha': eval.fecha_evaluacion.strftime('%d/%m/%Y'),
            'puntos': eval.get_total_puntos(),
            'porcentaje': eval.get_porcentaje_funcionalidad(),
            'nivel': eval.get_interpretacion()['nivel']
        })
    
    evaluations_json = json.dumps(evaluations_data)
    
    # Lista de actividades
    actividades = [
        "Trabajo usual, domestico o escuela",
        "Pasatiempos, recreación o deportes",
        "Entrar o salir del baño",
        "Andar entre cuartos",
        "Ponerse zapatos o calcetines",
        "Ponerse en cuclillas",
        "Levantar objeto del piso",
        "Actividades ligeras domésticas",
        "Actividades pesadas domésticas",
        "Entrar o salir de un coche",
        "Caminar 2 cuadras",
        "Caminar una milla",
        "Subir o bajar 10 escalones",
        "Estar de pie por 1 hora",
        "Estar sentado por 1 hora",
        "Correr sobre suelo plano",
        "Correr sobre suelo desigual",
        "Hacer vueltas bruscas corriendo",
        "Saltar",
        "Darse la vuelta en la cama"
    ]

    handler.auditar_consulta('LEFS')
    return render(request, 'CuestionarioLEFS.html', {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluations_json': evaluations_json,
        'evaluations_count': evaluations_count,
        'evaluaciones': evaluaciones,
        'actividades': actividades
    })


def _procesar_lefs_post(request, paciente, clinico):
    """Procesa las acciones POST para LEFS"""
    from .models import EvaluacionLEFS
    
    action = request.POST.get('action', 'guardar')
    
    try:
        # Obtener los valores de las 20 actividades
        actividades = {}
        for i in range(1, 21):
            campo_nombre = f'actividad_{i}'
            valor = request.POST.get(campo_nombre)
            
            if valor is None or valor == '':
                messages.error(request, f'Debe completar todas las actividades del cuestionario. Falta la actividad {i}.')
                return redirect(f"{reverse('lefs')}?rut={paciente.rut}")
            
            try:
                actividades[campo_nombre] = int(valor)
            except ValueError:
                messages.error(request, f'Valor inválido en la actividad {i}.')
                return redirect(f"{reverse('lefs')}?rut={paciente.rut}")
        
        # Obtener notas clínicas opcionales
        notas_clinicas = request.POST.get('notas_clinicas', '')
        
        # Crear nueva evaluación
        evaluacion = EvaluacionLEFS.objects.create(
            paciente=paciente,
            clinico=clinico,
            notas_clinicas=notas_clinicas,
            actividad_1_trabajo=actividades['actividad_1'],
            actividad_2_pasatiempos=actividades['actividad_2'],
            actividad_3_banio=actividades['actividad_3'],
            actividad_4_andar_cuartos=actividades['actividad_4'],
            actividad_5_zapatos=actividades['actividad_5'],
            actividad_6_cuclillas=actividades['actividad_6'],
            actividad_7_levantar_objeto=actividades['actividad_7'],
            actividad_8_actividades_ligeras=actividades['actividad_8'],
            actividad_9_actividades_pesadas=actividades['actividad_9'],
            actividad_10_coche=actividades['actividad_10'],
            actividad_11_caminar_2cuadras=actividades['actividad_11'],
            actividad_12_caminar_milla=actividades['actividad_12'],
            actividad_13_escalones=actividades['actividad_13'],
            actividad_14_estar_pie=actividades['actividad_14'],
            actividad_15_estar_sentado=actividades['actividad_15'],
            actividad_16_correr_plano=actividades['actividad_16'],
            actividad_17_correr_desigual=actividades['actividad_17'],
            actividad_18_vueltas_bruscas=actividades['actividad_18'],
            actividad_19_saltar=actividades['actividad_19'],
            actividad_20_vuelta_cama=actividades['actividad_20']
        )
        
        # Obtener interpretación para el mensaje
        interpretacion = evaluacion.get_interpretacion()
        total = evaluacion.get_total_puntos()
        porcentaje = evaluacion.get_porcentaje_funcionalidad()

        auditar_cuestionario_edicion(request, paciente, 'LEFS', 'nueva evaluación')
        
        messages.success(
            request, 
            f'Evaluación LEFS guardada correctamente. '
            f'Resultado: {total}/80 puntos ({porcentaje}%) - {interpretacion["nivel"]}'
        )
        
    except Exception as e:
        messages.error(request, f'Error al procesar la evaluación: {str(e)}')
    
    return redirect(f"{reverse('lefs')}?rut={paciente.rut}")
