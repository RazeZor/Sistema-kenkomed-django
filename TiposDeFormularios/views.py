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
    """Vista para manejar el cuestionario PSFS con actividades manuales"""
    handler = BaseEvaluacionHandler(request)
    
    paciente = handler.obtener_paciente()
    if not paciente:
        return HttpResponse('Paciente no encontrado', status=404)
    
    cuestionario = CuestionarioPSFS.objects.filter(paciente=paciente).first()
    
    if request.method == 'POST':
        return _procesar_psfs_post(request, paciente, cuestionario)
    
    # Preparar datos para renderizado
    sesiones = _obtener_sesiones_psfs(cuestionario) if cuestionario else []
    
    return render(request, 'CuestionarioPSFS.html', {
        'rut': paciente.rut,
        'actividad1': cuestionario.actividad_1 if cuestionario else '',
        'actividad2': cuestionario.actividad_2 if cuestionario else '',
        'actividad3': cuestionario.actividad_3 if cuestionario else '',
        'sesiones': sesiones,
        'evaluacion_existente': cuestionario is not None,
        'nota': cuestionario.NotaCuestionarioPSFS if cuestionario else None
    })


def _procesar_psfs_post(request, paciente, cuestionario):
    """Procesa las acciones POST para PSFS con actividades manuales"""
    print("\n=== INICIO _procesar_psfs_post ===")
    print(f"Método: {request.method}")
    print(f"Datos POST: {request.POST}")
    
    action = request.POST.get('action', '')
    print(f"Acción: {action}")
    
    # Obtener actividades del formulario
    actividad_1 = request.POST.get('actividad_1', '').strip()
    actividad_2 = request.POST.get('actividad_2', '').strip()
    actividad_3 = request.POST.get('actividad_3', '').strip()
    
    print(f"Actividades recibidas: {actividad_1}, {actividad_2}, {actividad_3}")
    
    # Validar que se hayan ingresado las actividades si es una nueva evaluación
    if action == 'guardar' and not all([actividad_1, actividad_2, actividad_3]):
        error_msg = "Debe ingresar las tres actividades para continuar."
        print(error_msg)
        messages.error(request, error_msg)
        return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")
    
    # Manejar la acción de guardar nota (tanto para 'GuardarNota' como para cuando solo se envía 'notes')
    if action == 'GuardarNota' or 'notes' in request.POST:
        notaPSFS = request.POST.get('notes', '').strip()
        if not notaPSFS and 'nota_adicional' in request.POST:
            notaPSFS = request.POST.get('nota_adicional', '').strip()
            
        if not notaPSFS:
            messages.error(request, "No se proporcionó ninguna nota para guardar.")
        elif _actualizar_nota_psfs(paciente, notaPSFS):
            messages.success(request, "Nota guardada correctamente.")
        else:
            messages.error(request, "Error al guardar la nota. Asegúrese de que el cuestionario existe.")
        return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")
    
    # Obtener puntajes solo si no es una acción de guardar nota
    puntajes = {
        'actividad_1': request.POST.getlist('rango1'),
        'actividad_2': request.POST.getlist('rango2'),
        'actividad_3': request.POST.getlist('rango3'),
        'total': request.POST.getlist('total_score')
    }
    
    print(f"Puntajes recibidos: {puntajes}")
    notaPSFS = request.POST.get('nota_adicional', '')
    
    try:
        if action == 'guardar':
            # Crear nueva evaluación
            CuestionarioPSFS.objects.create(
                paciente=paciente,
                fecha_creacion=datetime.now().date(),
                actividad_1=actividad_1,
                actividad_2=actividad_2,
                actividad_3=actividad_3,
                puntaje_actividad_1=json.dumps(puntajes['actividad_1']),
                puntaje_actividad_2=json.dumps(puntajes['actividad_2']),
                puntaje_actividad_3=json.dumps(puntajes['actividad_3']),
                puntajeTotal=json.dumps(puntajes['total']),
                NotaCuestionarioPSFS=notaPSFS
            )
            messages.success(request, "Cuestionario guardado correctamente.")
            
        elif action == 'actualizar':
            # Actualizar evaluación existente
            if not cuestionario:
                cuestionario = get_object_or_404(CuestionarioPSFS, paciente=paciente)
            
            # Actualizar actividades si se proporcionaron
            if actividad_1:
                cuestionario.actividad_1 = actividad_1
            if actividad_2:
                cuestionario.actividad_2 = actividad_2
            if actividad_3:
                cuestionario.actividad_3 = actividad_3
                
            _actualizar_puntajes_psfs(cuestionario, puntajes)
            
            # Actualizar la nota si se proporcionó
            if 'nota_adicional' in request.POST:
                cuestionario.NotaCuestionarioPSFS = notaPSFS
                
            cuestionario.save()
            messages.success(request, "Cuestionario actualizado correctamente.")
            
    except Exception as e:
        messages.error(request, f"Error al procesar el cuestionario: {str(e)}")
        
    return redirect(f"{reverse('gestionar_psfs')}?rut={paciente.rut}")


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


def _obtener_sesiones_psfs(cuestionario):
    """Obtiene las sesiones formateadas para PSFS"""
    if not cuestionario:
        return []
    
    sesiones = []
    try:
        # Obtener todos los puntajes de las actividades
        puntajes_1 = json.loads(cuestionario.puntaje_actividad_1 or '[]')
        puntajes_2 = json.loads(cuestionario.puntaje_actividad_2 or '[]')
        puntajes_3 = json.loads(cuestionario.puntaje_actividad_3 or '[]')
        totales = json.loads(cuestionario.puntajeTotal or '[]')
        
        # Determinar el número de sesiones (máxima longitud entre los arrays)
        num_sesiones = max(len(puntajes_1), len(puntajes_2), len(puntajes_3), len(totales))
        
        # Crear una sesión para cada conjunto de puntajes
        for i in range(num_sesiones):
            # Obtener los puntajes para esta sesión o usar 0 si no existen
            p1 = int(puntajes_1[i]) if i < len(puntajes_1) else 0
            p2 = int(puntajes_2[i]) if i < len(puntajes_2) else 0
            p3 = int(puntajes_3[i]) if i < len(puntajes_3) else 0
            total = float(totales[i]) if i < len(totales) else 0
            
            sesiones.append({
                'numero': i + 1,
                'puntaje_1': p1,
                'puntaje_2': p2,
                'puntaje_3': p3,
                'total': total,
                'fecha': cuestionario.fecha_creacion.strftime('%d/%m/%Y')
            })
            
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error al procesar los puntajes PSFS: {e}")
        return []
    
    return sesiones


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

    if evaluacion_existente:
        cuestionario_actual = CuestionarioScrenning.objects.get(paciente=paciente)

    if request.method == "POST":
        return _procesar_screening_post(request, paciente, handler.clinico)

    # Obtener todas las evaluaciones del paciente

    toda_evaluacion_existente = CuestionarioScrenning.objects.filter(paciente=paciente)
    # Si existe la evaluación actual, generar alerta
    alerta = generar_alerta(cuestionario_actual.Puntaje_Sesion) if cuestionario_actual else None

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

                messages.success(request, 'Evaluación guardada correctamente.')

            elif action == 'delete':
                # eliminar por índice
                index = int(request.POST.get('index', -1))
                if cuestionario and 0 <= index < len(cuestionario.estado_por_sesion):
                    estado = cuestionario.estado_por_sesion
                    estado.pop(index)
                    cuestionario.estado_por_sesion = estado
                    cuestionario.save()
                    messages.success(request, 'Evaluación eliminada.')
                else:
                    messages.error(request, 'Índice no válido para eliminar.')

            elif action == 'clear':
                if cuestionario:
                    cuestionario.estado_por_sesion = []
                    cuestionario.save()
                messages.success(request, 'Historial limpiado.')

        except Exception as e:
            messages.error(request, f'Error al procesar la petición: {str(e)}')

        return HttpResponseRedirect(request.get_full_path())

    # Render GET: inyectar las evaluaciones (serializadas) en el template
    import json as _json
    evaluations_json = _json.dumps(evaluations)

    return render(request, "CuestionarioENA.html", {
        'rut': paciente.rut,
        'paciente': paciente,
        'evaluations_json': evaluations_json,
        'evaluations': evaluations,
        'clinico_actual': handler.clinico
    })