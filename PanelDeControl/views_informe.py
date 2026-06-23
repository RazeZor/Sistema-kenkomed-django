from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from Login.models import Paciente, formularioClinico
from django.contrib import messages
import json
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from clinicas.utils import obtener_paciente_por_rut
from clinicas.branding import url_logo_clinica
from Login.auditoria import registrar_acceso


def _parse_json_list(value):
    """Normaliza un JSONField que puede venir como lista, string JSON o texto plano."""
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [str(parsed)]
        except (json.JSONDecodeError, TypeError):
            return [value]
    return [str(value)]

@requiere_clinico
def RenderInforme(request):
    rut = request.GET.get('rut', '') or request.POST.get('rut', '')
    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        return HttpResponseForbidden("No tienes permisos para ver el informe de este paciente.")

    registrar_acceso(request, paciente, 'informe')

    try:
        formulario = formularioClinico.objects.get(paciente=paciente)
        
        opinionproblemaEnfermead = CreenciaDolor(formulario.opinionProblemaEnfermeda)
        
        caracteristicasDolor = json.loads(formulario.caracteristicasDeDolor)
        MensajecaracteristicasDolor = Neuropaticas(caracteristicasDolor)
        
        condicionesSalud1 = json.loads(formulario.TiposDeEnfermedades)
        MensajeCondicionesSalud = condicionesSalud(condicionesSalud1)

        ResultadosSueño = ResultSueño(formulario.despertares,formulario.hora_acostarse,formulario.tiempo_dormirse,formulario.hora_despertar,formulario.hora_levantarse)
        
        mensajeEVPER = Respuesta_evitativo_persistente(formulario.parametros)
        
        # Análisis de Determinantes Sociales de Salud (DSS)
        mensajeDSS = AnalisisDSS(
            formulario.pregunta1_nivelDeSalud,
            formulario.pregunta3_frecuencia_De_Suenio,
            formulario.pregunta4_opinion_peso_actual,
            formulario.pregunta5_ConsumoComidaRapida
        )
        
        MensajeNicotina = "no tiene" if formulario.nicotinaPreocupacion is None else formulario.nicotinaPreocupacion
        mensajeAcoholP = "no tiene" if formulario.AlcoholPreocupacion is None else formulario.AlcoholPreocupacion
        mensajeDrogasP = "no tiene" if formulario.DrogasPreocupacion is None else formulario.DrogasPreocupacion
        mensajeMarihuanaP = "no tiene" if formulario.marihuanaPreocupacion is None else formulario.marihuanaPreocupacion
        
        # Ubicación + Intensidad
        ubicacionDolor = json.loads(formulario.ubicacionDolor)
        intensidadDolor = json.loads(formulario.dolorIntensidad)
        ubicacion_intensidad_list = "<ul>"

        min_len = min(len(ubicacionDolor), len(intensidadDolor))
        for i in range(min_len):
            ubicacion = ubicacionDolor[i]
            intensidad = intensidadDolor[i]
            ubicacion_intensidad_list += f"<li>{ubicacion} - {intensidad}</li>"

        if len(ubicacionDolor) != len(intensidadDolor):
            ubicacion_intensidad_list += "<li><strong>Error:</strong> Las listas no coinciden en longitud</li>"

        ubicacion_intensidad_list += "</ul>"
        
        context = {
            'paciente': paciente,
            'formulario': formulario,
            'medicamentos': _parse_json_list(formulario.medicamentos),
            'ubicacion_intensidad': ubicacion_intensidad_list,
            'MensajecaracteristicasDolor': MensajecaracteristicasDolor,
            'MensajeCondicionesSalud': MensajeCondicionesSalud,
            'opinionproblemaEnfermead': opinionproblemaEnfermead,
            'mensajeEVPER': mensajeEVPER,
            'mensajeDSS': mensajeDSS,
            'MensajeNicotina': MensajeNicotina,
            'mensajeAcoholP': mensajeAcoholP,
            'mensajeDrogasP': mensajeDrogasP,
            'mensajeMarihuanaP': mensajeMarihuanaP,
            'ResultadosSueño': ResultadosSueño,
            'encontrado': True
        }

    except formularioClinico.DoesNotExist:
        context = {
            'encontrado': False,
            'mensaje': "No se encontró el formulario clínico de este paciente."
        }

    return render(request, 'informe.html', context)


@requiere_clinico
def RenderFichaClinica(request):
    """
    Ficha Clínica Profesional completa.
    Compila TODA la información del paciente: datos personales, anamnesis,
    sesiones kinésicas, cuestionarios, diagnóstico y alta.
    """
    from SesionesKinesicas.models import SesionKinesica
    from TiposDeFormularios.models import EvaluacionLEFS, EvaluacionOswestry
    from Login.models import (
        Clinico, CuestionarioPSFS, Groc, CuestionarioEQ_5D,
        CuestionarioBarthel, CuestionarioScrenning, CuestionarioEvaluacionENA,
        RecetaMedica, Notas,
    )

    rut = request.GET.get('rut', '') or request.POST.get('rut', '')
    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        return HttpResponseForbidden("No tienes permisos para ver la ficha clínica de este paciente.")

    registrar_acceso(request, paciente, 'ficha')

    rut_sesion = request.session.get('rut_clinico')
    clinico_emisor = Clinico.objects.filter(rut=rut_sesion).first() if rut_sesion else None
    if not clinico_emisor:
        clinico_emisor = paciente.clinico_creador

    clinica = paciente.clinica

    context = {
        'paciente': paciente,
        'clinica': clinica,
        'clinico': paciente.clinico_creador,
        'clinico_emisor': clinico_emisor,
        'logo_clinica_url': url_logo_clinica(clinica, request),
        'encontrado': True,
        'ubicacion_intensidad_pares': [],
    }

    # === Formulario Clínico (Anamnesis) ===
    try:
        formulario = formularioClinico.objects.get(paciente=paciente)
        context['formulario'] = formulario
        context['tiene_anamnesis'] = True

        ubicacion_dolor = []
        dolor_intensidad = []
        try:
            ubicacion_dolor = json.loads(formulario.ubicacionDolor) if formulario.ubicacionDolor else []
        except (json.JSONDecodeError, TypeError):
            pass
        try:
            dolor_intensidad = json.loads(formulario.dolorIntensidad) if formulario.dolorIntensidad else []
        except (json.JSONDecodeError, TypeError):
            pass

        context['ubicacionDolor'] = ubicacion_dolor
        context['dolorIntensidad'] = dolor_intensidad
        context['ubicacion_intensidad_pares'] = [
            {
                'ubicacion': u,
                'intensidad': dolor_intensidad[i] if i < len(dolor_intensidad) else '—',
            }
            for i, u in enumerate(ubicacion_dolor)
        ]

        try:
            context['caracteristicasDeDolor'] = json.loads(formulario.caracteristicasDeDolor) if formulario.caracteristicasDeDolor else []
        except (json.JSONDecodeError, TypeError):
            context['caracteristicasDeDolor'] = []

        try:
            context['TiposDeEnfermedades'] = json.loads(formulario.TiposDeEnfermedades) if formulario.TiposDeEnfermedades else []
        except (json.JSONDecodeError, TypeError):
            context['TiposDeEnfermedades'] = []

        try:
            context['medicamentos'] = _parse_json_list(formulario.medicamentos)
        except (json.JSONDecodeError, TypeError):
            context['medicamentos'] = []

        try:
            context['actividades_afectadas'] = json.loads(formulario.actividades_afectadas) if formulario.actividades_afectadas else []
        except (json.JSONDecodeError, TypeError):
            context['actividades_afectadas'] = []

    except formularioClinico.DoesNotExist:
        context['tiene_anamnesis'] = False

    # === Sesiones Kinésicas ===
    sesiones = SesionKinesica.objects.filter(paciente=paciente).order_by('numero_sesion')
    context['sesiones'] = sesiones
    context['total_sesiones'] = sesiones.count()
    context['primera_sesion'] = sesiones.filter(es_primera_sesion=True).first()
    context['sesion_final'] = sesiones.filter(es_sesion_final=True).last()

    # === Cuestionarios ===
    try:
        context['psfs'] = CuestionarioPSFS.objects.get(paciente=paciente)
    except CuestionarioPSFS.DoesNotExist:
        pass

    try:
        context['groc'] = Groc.objects.get(paciente=paciente)
    except Groc.DoesNotExist:
        pass

    try:
        context['eq5d'] = CuestionarioEQ_5D.objects.get(paciente=paciente)
    except CuestionarioEQ_5D.DoesNotExist:
        pass

    try:
        context['barthel'] = CuestionarioBarthel.objects.get(paciente=paciente)
    except CuestionarioBarthel.DoesNotExist:
        pass

    try:
        context['screening'] = CuestionarioScrenning.objects.get(paciente=paciente)
    except CuestionarioScrenning.DoesNotExist:
        pass

    try:
        context['ena'] = CuestionarioEvaluacionENA.objects.get(paciente=paciente)
    except CuestionarioEvaluacionENA.DoesNotExist:
        pass

    context['evaluaciones_lefs'] = list(
        EvaluacionLEFS.objects.filter(paciente=paciente).select_related('clinico').order_by('-fecha_evaluacion')
    )
    context['evaluaciones_oswestry'] = list(
        EvaluacionOswestry.objects.filter(paciente=paciente).select_related('clinico').order_by('-fecha_evaluacion')
    )

    try:
        context['receta'] = RecetaMedica.objects.select_related('clinico').get(paciente=paciente)
    except RecetaMedica.DoesNotExist:
        pass

    try:
        context['notas'] = Notas.objects.get(paciente=paciente)
    except Notas.DoesNotExist:
        pass

    return render(request, 'ficha_clinica.html', context)


# === Funciones de análisis clínico para informe ===

def ResultSueño(despertares, hora_acostarse, tiempo_dormirse, hora_despertar, hora_levantarse):
    try:
        mensajes = []
        if hora_acostarse == "despues_0000":
            mensajes.append("El paciente se acuesta después de medianoche, lo que puede afectar la calidad del sueño.")
        if tiempo_dormirse in ["30_60", "mas_60"]:
            mensajes.append("El paciente tarda más de 30 minutos en dormirse, lo que puede indicar insomnio de conciliación.")
        if hora_despertar == "antes_0500":
            mensajes.append("El paciente se despierta antes de las 05:00 hrs, lo que podría reflejar sueño insuficiente.")
        if hora_levantarse in ["30_60", "mas_60"]:
            mensajes.append("El paciente permanece mucho tiempo en cama después de despertar, lo que puede reflejar cansancio.")
        if despertares == "2_3":
            mensajes.append("El paciente se despierta 2-3 veces por noche, interrumpiendo el descanso.")
        elif despertares == "mas_3":
            mensajes.append("El paciente se despierta más de 3 veces por noche, indicando sueño muy fragmentado.")

        if not mensajes:
            return {
                'status': 'success',
                'title': 'Sueño sin Dificultades',
                'message': 'El paciente no presenta dificultades relevantes para dormir.',
                'items': []
            }
        else:
            return {
                'status': 'warning',
                'title': 'Observaciones sobre el Sueño',
                'items': mensajes
            }
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Procesamiento',
            'message': f'Error al procesar el formulario de sueño: {str(e)}',
            'items': []
        }


def Neuropaticas(caracteristicasDolor):
    try:
        caracteristicas_neuropaticas = {
            "ardiente": "sensación de quemazón",
            "corriente": "sensación de corriente eléctrica o descarga",
            "adormecimiento": "adormecimiento o entumecimiento",
            "Hormigueo": "hormigueo o parestesias"
        }
        caracteristicas_detectadas = []
        for caracteristica in caracteristicasDolor:
            if caracteristica in caracteristicas_neuropaticas:
                caracteristicas_detectadas.append(
                    f"{caracteristica.capitalize()}: {caracteristicas_neuropaticas[caracteristica]}"
                )
        if caracteristicas_detectadas:
            return {
                'status': 'warning',
                'title': 'Posible componente neuropático del dolor',
                'message': 'Se detectaron las siguientes características neuropáticas:',
                'items': caracteristicas_detectadas,
                'recommendation': 'Aplicar la Escala DN4 (Douleur Neuropathique 4) para confirmar el diagnóstico de dolor neuropático. Esta escala sugiere dolor neuropático si el puntaje es >= 4/10.'
            }
        return {
            'status': 'success',
            'title': 'Dolor Nociceptivo',
            'message': 'No se detectaron características de dolor neuropático en las respuestas del paciente.',
            'items': []
        }
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar características del dolor: {str(e)}',
            'items': []
        }


def condicionesSalud(condicionesSalud):
    try:
        recomendaciones_detalladas = {
            "Fibromialgia": {
                "titulo": "Fibromialgia",
                "razon": "La fibromialgia es un síndrome de dolor crónico generalizado que requiere evaluación específica.",
                "herramienta": "Cuestionario de Impacto de Fibromialgia (FIQ)",
                "justificacion": "Este instrumento evalúa el impacto funcional, síntomas y calidad de vida específicos de fibromialgia."
            },
            "Hormigueos o adormecimiento": {
                "titulo": "Hormigueos o adormecimiento",
                "razon": "Los síntomas de parestesias sugieren posible afectación del sistema nervioso periférico.",
                "herramienta": "Escala DN4 (Douleur Neuropathique 4)",
                "justificacion": "Permite identificar y cuantificar el componente neuropático del dolor mediante criterios validados."
            },
            "diabetes": {
                "titulo": "Diabetes",
                "razon": "La diabetes es una causa común de neuropatía periférica (30-50% de pacientes diabéticos).",
                "herramienta": "Escala DN4 y evaluación de neuropatía diabética",
                "justificacion": "La neuropatía diabética afecta la sensibilidad y puede causar dolor neuropático crónico que requiere manejo específico."
            },
            "Ansiedad": {
                "titulo": "Ansiedad",
                "razon": "La ansiedad puede amplificar la percepción del dolor y afectar la adherencia al tratamiento.",
                "herramienta": "Escala de Ansiedad y Depresión Hospitalaria (HADS) o GAD-7",
                "justificacion": "Existe una relación bidireccional entre ansiedad y dolor crónico. El tratamiento integral debe abordar ambos aspectos."
            },
            "Depresion": {
                "titulo": "Depresión",
                "razon": "La depresión está presente en 30-60% de pacientes con dolor crónico y afecta el pronóstico.",
                "herramienta": "Escala de Ansiedad y Depresión Hospitalaria (HADS) o PHQ-9",
                "justificacion": "La comorbilidad dolor-depresión requiere abordaje integrado para mejorar resultados terapéuticos."
            }
        }
        condiciones_detectadas = []
        for condicion in condicionesSalud:
            if condicion in recomendaciones_detalladas:
                condiciones_detectadas.append(recomendaciones_detalladas[condicion])
        if condiciones_detectadas:
            return {
                'status': 'warning',
                'title': 'Evaluaciones complementarias recomendadas',
                'message': f'Se detectaron {len(condiciones_detectadas)} condición(es) de salud que requieren evaluación específica:',
                'items': condiciones_detectadas
            }
        return {
            'status': 'success',
            'title': 'Condiciones de Salud Estables',
            'message': 'No se detectaron condiciones de salud que requieran evaluaciones complementarias específicas.',
            'items': []
        }
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar condiciones de salud: {str(e)}',
            'items': []
        }


def CreenciaDolor(CreenciaDolor):
    try:
        if CreenciaDolor == 'si':
            return {
                'status': 'warning',
                'title': 'Creencia de dolor no diagnosticado',
                'message': 'El paciente cree que tiene un problema de salud o dolor que no ha sido diagnosticado.',
                'implication': 'Esta creencia puede indicar catastrofización del dolor, un proceso cognitivo-afectivo caracterizado por magnificación de la amenaza del dolor, rumiación y sensación de impotencia.',
                'bullets': [
                    'Mayor intensidad del dolor percibido',
                    'Peor respuesta al tratamiento',
                    'Mayor discapacidad funcional',
                    'Riesgo de cronificación del dolor'
                ],
                'recommendation': 'Pain Catastrophizing Scale (PCS)',
                'justification': 'La PCS evalúa rumiación, magnificación e impotencia. Un puntaje >= 30 indica catastrofización significativa.'
            }
        else:
            return {
                'status': 'success',
                'title': 'Percepción Realista',
                'message': 'El paciente no manifiesta creencias de dolor no diagnosticado, lo que sugiere una percepción más realista de su condición.'
            }
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar creencias sobre el dolor: {str(e)}'
        }


def Respuesta_evitativo_persistente(respuestas):
    try:
        EVITATIVAS = "evitativo"
        PERSISTENTES = "persistente"
        evitativo = 0
        persistente = 0

        for respuesta in respuestas:
            respuesta_limpia = respuesta.strip().lower()
            if respuesta_limpia == EVITATIVAS:
                evitativo += 1
            elif respuesta_limpia == PERSISTENTES:
                persistente += 1

        total_respuestas = evitativo + persistente
        if total_respuestas == 0:
            return {
                'status': 'info',
                'title': 'Sin datos suficientes',
                'message': 'No se detectaron respuestas válidas para evaluar el patrón de conducta ante el dolor.'
            }

        porcentaje_evitativo = round((evitativo / total_respuestas) * 100, 1)
        porcentaje_persistente = round((persistente / total_respuestas) * 100, 1)

        if evitativo > persistente:
            diferencia = evitativo - persistente
            nivel = "marcada" if diferencia >= 3 else "leve"
            return {
                'status': 'warning',
                'title': f'Conducta predominantemente EVITATIVA ({nivel})',
                'stats': [
                    f'Respuestas evitativas: {evitativo} de {total_respuestas} ({porcentaje_evitativo}%)',
                    f'Respuestas persistentes: {persistente} de {total_respuestas} ({porcentaje_persistente}%)'
                ],
                'interpretation': 'El paciente presenta un patrón de kinesiofobia (miedo al movimiento), caracterizado por evitación de actividades que podrían causar dolor.',
                'bullets': [
                    'Reduce la capacidad funcional progresivamente',
                    'Aumenta el desacondicionamiento físico',
                    'Perpetúa el ciclo miedo-evitación-discapacidad'
                ],
                'recommendations': [
                    'Exposición gradual progresiva con jerarquía de actividades temidas.',
                    'Educación en neurociencia del dolor para reducir el miedo.',
                    'Reestructuración cognitiva de creencias limitantes.',
                    'Aplicar Tampa Scale of Kinesiophobia (TSK) si es necesario.'
                ]
            }
        elif persistente > evitativo:
            diferencia = persistente - evitativo
            nivel = "marcada" if diferencia >= 3 else "leve"
            return {
                'status': 'danger',
                'title': f'Conducta predominantemente PERSISTENTE ({nivel})',
                'stats': [
                    f'Respuestas persistentes: {persistente} de {total_respuestas} ({porcentaje_persistente}%)',
                    f'Respuestas evitativas: {evitativo} de {total_respuestas} ({porcentaje_evitativo}%)'
                ],
                'interpretation': 'El paciente presenta un patrón de sobreactividad o endurance, caracterizado por ignorar las señales de dolor y continuar con actividades hasta el agotamiento.',
                'bullets': [
                    'Genera ciclos de sobreactividad seguidos de colapso ("boom-bust")',
                    'Aumenta la inflamación y el daño tisular',
                    'Dificulta la percepción de límites corporales'
                ],
                'recommendations': [
                    'Pacing (dosificación de actividades): Enseñar a distribuir actividades en el tiempo.',
                    'Entrenar en la identificación temprana de fatiga/dolor.',
                    'Aplicar bloques de tiempo (alternar actividad y descanso).',
                    'Mindfulness para mejorar conciencia corporal.'
                ]
            }
        else:
            return {
                'status': 'success',
                'title': 'Conducta EQUILIBRADA',
                'stats': [
                    f'Respuestas evitativas: {evitativo} de {total_respuestas} ({porcentaje_evitativo}%)',
                    f'Respuestas persistentes: {persistente} de {total_respuestas} ({porcentaje_persistente}%)'
                ],
                'interpretation': 'El paciente muestra un patrón adaptativo de respuesta al dolor, con capacidad para ajustar actividad según sus límites.',
                'bullets': [
                    'Ajusta su nivel de actividad según las señales corporales',
                    'Evita tanto la kinesiofobia como la sobreexigencia',
                    'Demuestra flexibilidad conductual'
                ],
                'recommendations': [
                    'Reforzar estrategias actuales adaptativas.',
                    'Mantener el automonitoreo de síntomas.',
                    'Prevención de recaídas identificando situaciones desencadenantes.'
                ]
            }
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar patrón de conducta: {str(e)}'
        }


def AnalisisDSS(nivel_salud, frecuencia_sueno, opinion_peso, consumo_comida_rapida):
    try:
        observaciones = []
        nivel_riesgo = "bajo"
        campos_evaluados = 0
        campos_totales = 4
        
        if nivel_salud and nivel_salud.strip():
            campos_evaluados += 1
            nivel_salud_lower = nivel_salud.lower().strip()
            if "muy afectada" in nivel_salud_lower or "problemas graves" in nivel_salud_lower:
                observaciones.append({
                    "categoria": "Salud percibida muy deteriorada",
                    "hallazgo": "El paciente percibe su salud como muy afectada con problemas graves.",
                    "implicacion": "Asociado con peor pronóstico funcional y autopercepción negativa.",
                    "recomendacion": "Evaluación integral multidisciplinaria. Descartar trastornos emocionales."
                })
                nivel_riesgo = "alto"
            elif "muchas molestias" in nivel_salud_lower or "limitaciones" in nivel_salud_lower:
                observaciones.append({
                    "categoria": "Salud percibida deteriorada",
                    "hallazgo": "El paciente reporta muchas molestias o limitaciones en su vida diaria.",
                    "implicacion": "Impacto funcional moderado-grave.",
                    "recomendacion": "Establecer objetivos funcionales específicos."
                })
                if nivel_riesgo != "alto":
                    nivel_riesgo = "moderado"
        
        if frecuencia_sueno and frecuencia_sueno.strip():
            campos_evaluados += 1
            frecuencia_sueno_lower = frecuencia_sueno.lower().strip()
            if frecuencia_sueno_lower == "siempre":
                observaciones.append({
                    "categoria": "Somnolencia diurna excesiva severa",
                    "hallazgo": "El paciente siempre se siente cansado durante el día.",
                    "implicacion": "Puede indicar trastornos del sueño no diagnosticados.",
                    "recomendacion": "Derivar a especialista en medicina del sueño. Escala Epworth."
                })
                nivel_riesgo = "alto"
            elif frecuencia_sueno_lower == "frecuentemente":
                observaciones.append({
                    "categoria": "Somnolencia diurna excesiva moderada",
                    "hallazgo": "El paciente frecuentemente experimenta somnolencia.",
                    "implicacion": "Higiene de sueño deficiente o fatiga crónica.",
                    "recomendacion": "Educar en higiene del sueño."
                })
                if nivel_riesgo != "alto":
                    nivel_riesgo = "moderado"
        
        if opinion_peso and opinion_peso.strip():
            campos_evaluados += 1
            opinion_peso_lower = opinion_peso.lower().strip()
            if "ganar mucho peso" in opinion_peso_lower:
                observaciones.append({
                    "categoria": "Deseo de ganancia de peso",
                    "hallazgo": "El paciente desea ganar mucho peso.",
                    "implicacion": "Riesgo de sarcopenia o pérdida de masa muscular.",
                    "recomendacion": "Evaluar estado nutricional y composición corporal."
                })
                if nivel_riesgo == "bajo":
                    nivel_riesgo = "moderado"
            elif "perder mucho peso" in opinion_peso_lower:
                observaciones.append({
                    "categoria": "Deseo de pérdida de peso",
                    "hallazgo": "El paciente desea perder mucho peso.",
                    "implicacion": "Posible sobrepeso u obesidad que aumenta carga articular.",
                    "recomendacion": "Calcular IMC, orientar ejercicio adaptado de bajo impacto."
                })
                if nivel_riesgo == "bajo":
                    nivel_riesgo = "moderado"
        
        if consumo_comida_rapida and consumo_comida_rapida.strip():
            campos_evaluados += 1
            consumo_comida_rapida_lower = consumo_comida_rapida.lower().strip()
            if "casi todos los dias" in consumo_comida_rapida_lower or "casi todos los días" in consumo_comida_rapida_lower:
                observaciones.append({
                    "categoria": "Patrón alimenticio de alto riesgo",
                    "hallazgo": "Consumo de comida rápida o alimentos procesados casi a diario.",
                    "implicacion": "Dieta proinflamatoria que puede empeorar dolor crónico.",
                    "recomendacion": "Educación en alimentación saludable, dieta mediterránea (antiinflamatoria)."
                })
                nivel_riesgo = "alto"
            elif "mas de la mitad" in consumo_comida_rapida_lower or "más de la mitad" in consumo_comida_rapida_lower:
                observaciones.append({
                    "categoria": "Patrón alimenticio de riesgo moderado",
                    "hallazgo": "Consumo de procesados más de la mitad de los días.",
                    "implicacion": "Dieta subóptima.",
                    "recomendacion": "Consejería nutricional para reducción gradual."
                })
                if nivel_riesgo != "alto":
                    nivel_riesgo = "moderado"
        
        if campos_evaluados == 0:
            return {
                'status': 'info',
                'title': 'Análisis de Determinantes Sociales de Salud',
                'nivel': 'DATOS INSUFICIENTES',
                'message': 'No se encontraron datos de estilo de vida para analizar.',
                'observaciones': [],
                'campos_evaluados': 0,
                'campos_totales': campos_totales
            }
        
        if not observaciones:
            return {
                'status': 'success',
                'title': 'Análisis de Determinantes Sociales de Salud',
                'nivel': 'Perfil favorable',
                'message': 'No se identificaron factores de riesgo de estilo de vida significativos.',
                'observaciones': [],
                'campos_evaluados': campos_evaluados,
                'campos_totales': campos_totales
            }
        
        if nivel_riesgo == "alto":
            status = 'danger'
            titulo_riesgo = "ALTO RIESGO"
        elif nivel_riesgo == "moderado":
            status = 'warning'
            titulo_riesgo = "RIESGO MODERADO"
        else:
            status = 'info'
            titulo_riesgo = "RIESGO BAJO"
        
        return {
            'status': status,
            'title': f'Análisis de Determinantes Sociales de Salud',
            'nivel': titulo_riesgo,
            'message': f'Se identificaron {len(observaciones)} áreas de preocupación relacionadas con el estilo de vida:',
            'observaciones': observaciones,
            'note': 'Abordar factores de estilo de vida ayuda a mejorar sustancialmente el pronóstico del paciente.',
            'campos_evaluados': campos_evaluados,
            'campos_totales': campos_totales
        }
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar determinantes sociales de salud: {str(e)}'
        }
