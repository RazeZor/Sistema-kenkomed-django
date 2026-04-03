from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from Login.models import Paciente,formularioClinico,Clinico
import json


def RenderInforme(request):
    
    rut = request.GET.get('rut', '') or request.POST.get('rut', '')
    paciente = get_object_or_404(Paciente, rut=rut)

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
        # INICIALIZA CONTEXT
        context = {
            'paciente': paciente,
            'formulario': formulario,
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

# funciones y algoritmo para las Respuesta de el informe 

def ResultSueño(despertares, hora_acostarse, tiempo_dormirse, hora_despertar, hora_levantarse):
    """
    Recibe los 5 campos del formulario de sueño como strings.
    Devuelve un diccionario con observaciones estructuradas.
    """
    try:
        mensajes = []

        # --- 1. Hora de acostarse ---
        if hora_acostarse == "despues_0000":
            mensajes.append("El paciente se acuesta después de medianoche, lo que puede afectar la calidad del sueño.")

        # --- 2. Tiempo en dormirse ---
        if tiempo_dormirse in ["30_60", "mas_60"]:
            mensajes.append("El paciente tarda más de 30 minutos en dormirse, lo que puede indicar insomnio de conciliación.")

        # --- 3. Hora de despertar ---
        if hora_despertar == "antes_0500":
            mensajes.append("El paciente se despierta antes de las 05:00 hrs, lo que podría reflejar sueño insuficiente.")

        # --- 4. Tiempo en levantarse ---
        if hora_levantarse in ["30_60", "mas_60"]:
            mensajes.append("El paciente permanece mucho tiempo en cama después de despertar, lo que puede reflejar cansancio.")

        # --- 5. Despertares nocturnos ---
        if despertares == "2_3":
            mensajes.append("El paciente se despierta 2-3 veces por noche, interrumpiendo el descanso.")
        elif despertares == "mas_3":
            mensajes.append("El paciente se despierta más de 3 veces por noche, indicando sueño muy fragmentado.")

        # --- Resultado final ---
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
    """
    Evalúa las características del dolor para detectar posibles componentes neuropáticos.
    """
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
                'recommendation': 'Aplicar la Escala DN4 (Douleur Neuropathique 4) para confirmar el diagnóstico de dolor neuropático. Esta escala validada permite diferenciar el dolor neuropático del nociceptivo mediante 10 ítems (7 relacionados con síntomas y 3 con el examen físico). Un puntaje ≥4/10 sugiere dolor neuropático.'
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
    """
    Analiza las condiciones de salud del paciente y genera recomendaciones
    de evaluaciones complementarias basadas en la evidencia clínica.
    """
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
                info = recomendaciones_detalladas[condicion]
                condiciones_detectadas.append(info)
        
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
    """
    Evalúa la percepción del paciente sobre su dolor y recomienda herramientas
    para evaluar catastrofización si es necesario.
    """
    try:
        if CreenciaDolor == 'si':
            return {
                'status': 'warning',
                'title': 'Creencia de dolor no diagnosticado',
                'message': 'El paciente cree que tiene un problema de salud o dolor que no ha sido diagnosticado.',
                'implication': 'Esta creencia puede indicar catastrofización del dolor, un proceso cognitivo-afectivo caracterizado por magnificación de la amenaza del dolor, rumiación y sensación de impotencia. La catastrofización se asocia con:',
                'bullets': [
                    'Mayor intensidad del dolor percibido',
                    'Peor respuesta al tratamiento',
                    'Mayor discapacidad funcional',
                    'Riesgo de cronificación del dolor'
                ],
                'recommendation': 'Pain Catastrophizing Scale (PCS)',
                'justification': 'La PCS es un cuestionario validado de 13 ítems que evalúa tres dimensiones de la catastrofización: rumiación, magnificación e impotencia. Un puntaje ≥30 indica catastrofización clínicamente significativa que requiere intervención cognitivo-conductual.'
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
    """
    Analiza las respuestas del paciente para determinar su patrón de conducta
    frente al dolor: evitativo, persistente o equilibrado.
    Proporciona análisis detallado con justificación clínica.
    """
    try:
        EVITATIVAS = "evitativo"
        PERSISTENTES = "persistente"
        evitativo = 0
        persistente = 0

        # Contar respuestas
        for respuesta in respuestas:
            respuesta_limpia = respuesta.strip().lower()
            if respuesta_limpia == EVITATIVAS:
                evitativo += 1
            elif respuesta_limpia == PERSISTENTES:
                persistente += 1

        total_respuestas = evitativo + persistente
        
        # Si no hay respuestas válidas
        if total_respuestas == 0:
            return {
                'status': 'info',
                'title': 'Sin datos suficientes',
                'message': 'No se detectaron respuestas válidas para evaluar el patrón de conducta ante el dolor. Se recomienda completar el cuestionario de conductas evitativas/persistentes.'
            }

        # Calcular porcentajes
        porcentaje_evitativo = round((evitativo / total_respuestas) * 100, 1)
        porcentaje_persistente = round((persistente / total_respuestas) * 100, 1)

        # Conducta predominantemente evitativa
        if evitativo > persistente:
            diferencia = evitativo - persistente
            nivel = "marcada" if diferencia >= 3 else "leve"
            return {
                'status': 'warning',
                'title': f'Conducta predominantemente EVITATIVA ({nivel})',
                'stats': [
                    f'Respuestas evitativas: {evitativo} de {total_respuestas} ({porcentaje_evitativo}%)',
                    f'Respuestas persistentes: {persistente} de {total_respuestas} ({porcentaje_persistente}%)',
                    f'Diferencia: {diferencia} respuestas a favor de evitación'
                ],
                'interpretation': 'El paciente presenta un patrón de kinesiofobia (miedo al movimiento), caracterizado por evitación de actividades que podrían causar dolor. Este comportamiento:',
                'bullets': [
                    'Reduce la capacidad funcional progresivamente',
                    'Aumenta el desacondicionamiento físico',
                    'Perpetúa el ciclo miedo-evitación-discapacidad',
                    'Puede llevar a aislamiento social y depresión'
                ],
                'recommendations': [
                    'Exposición gradual: Programa de reactivación progresiva con jerarquía de actividades temidas',
                    'Educación en neurociencia del dolor: Explicar mecanismos del dolor para reducir el miedo',
                    'Reestructuración cognitiva: Modificar creencias catastróficas sobre el movimiento',
                    'Establecer metas funcionales: Objetivos realistas y medibles de actividad',
                    'Considerar aplicar: Tampa Scale of Kinesiophobia (TSK) para cuantificar el miedo al movimiento'
                ]
            }
        
        # Conducta predominantemente persistente
        elif persistente > evitativo:
            diferencia = persistente - evitativo
            nivel = "marcada" if diferencia >= 3 else "leve"
            return {
                'status': 'danger',
                'title': f'Conducta predominantemente PERSISTENTE ({nivel})',
                'stats': [
                    f'Respuestas persistentes: {persistente} de {total_respuestas} ({porcentaje_persistente}%)',
                    f'Respuestas evitativas: {evitativo} de {total_respuestas} ({porcentaje_evitativo}%)',
                    f'Diferencia: {diferencia} respuestas a favor de persistencia'
                ],
                'interpretation': 'El paciente presenta un patrón de sobreactividad o endurance, caracterizado por ignorar las señales de dolor y continuar con actividades hasta el agotamiento. Este comportamiento:',
                'bullets': [
                    'Genera ciclos de sobreactividad seguidos de colapso ("boom-bust")',
                    'Aumenta la inflamación y el daño tisular',
                    'Prolonga los períodos de recuperación',
                    'Dificulta la percepción de límites corporales'
                ],
                'recommendations': [
                    'Pacing (dosificación de actividades): Enseñar a distribuir actividades en el tiempo',
                    'Reconocimiento de señales corporales: Entrenar en identificación temprana de fatiga/dolor',
                    'Establecer límites realistas: Definir umbrales de actividad sostenibles',
                    'Técnica de los "bloques de tiempo": Alternar períodos de actividad y descanso programados',
                    'Mindfulness: Mejorar la conciencia corporal y aceptación de limitaciones',
                    'Prevenir recaídas: Identificar triggers de sobreexigencia (perfeccionismo, presión social)'
                ]
            }
        
        # Conducta equilibrada (empate)
        else:
            return {
                'status': 'success',
                'title': 'Conducta EQUILIBRADA',
                'stats': [
                    f'Respuestas evitativas: {evitativo} de {total_respuestas} ({porcentaje_evitativo}%)',
                    f'Respuestas persistentes: {persistente} de {total_respuestas} ({porcentaje_persistente}%)',
                    'Distribución: Equilibrio perfecto entre ambos patrones'
                ],
                'interpretation': 'El paciente muestra un patrón adaptativo de respuesta al dolor, con capacidad para:',
                'bullets': [
                    'Ajustar su nivel de actividad según las señales corporales',
                    'Mantener un balance entre actividad y descanso',
                    'Evitar tanto la kinesiofobia como la sobreexigencia',
                    'Demostrar flexibilidad conductual'
                ],
                'recommendations': [
                    'Reforzar estrategias actuales: El paciente ya utiliza un enfoque adaptativo',
                    'Mantener autorregulación: Continuar con el automonitoreo de síntomas',
                    'Prevención de recaídas: Identificar situaciones que puedan alterar este equilibrio',
                    'Optimizar funcionalidad: Trabajar en incremento gradual de capacidades dentro del equilibrio'
                ]
            }
    
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar patrón de conducta: {str(e)}'
        }


def AnalisisDSS(nivel_salud, frecuencia_sueno, opinion_peso, consumo_comida_rapida):
    """
    Analiza los Determinantes Sociales de la Salud (DSS) basado en estilo de vida.
    Evalúa: nivel de salud percibido, calidad del sueño, percepción del peso y hábitos alimenticios.
    Proporciona recomendaciones basadas en evidencia para el clínico.
    """
    try:
        observaciones = []
        nivel_riesgo = "bajo"  # bajo, moderado, alto
        
        # --- 1. Análisis del nivel de salud percibido ---
        if nivel_salud:
            if "muy afectada" in nivel_salud.lower() or "problemas graves" in nivel_salud.lower():
                observaciones.append({
                    "categoria": "Salud percibida muy deteriorada",
                    "hallazgo": "El paciente percibe su salud como muy afectada con problemas graves que dificultan casi todas sus actividades diarias.",
                    "implicacion": "La autopercepción negativa de salud es un predictor independiente de mortalidad y está asociada con peor pronóstico funcional.",
                    "recomendacion": "Evaluación integral multidisciplinaria. Considerar derivación a salud mental por posible depresión asociada."
                })
                nivel_riesgo = "alto"
            elif "muchas molestias" in nivel_salud.lower() or "limitaciones" in nivel_salud.lower():
                observaciones.append({
                    "categoria": "Salud percibida deteriorada",
                    "hallazgo": "El paciente reporta muchas molestias o limitaciones que afectan significativamente su vida diaria.",
                    "implicacion": "Indica impacto funcional importante que puede perpetuar el ciclo de dolor y discapacidad.",
                    "recomendacion": "Establecer objetivos funcionales específicos y medibles. Implementar programa de rehabilitación gradual."
                })
                if nivel_riesgo != "alto":
                    nivel_riesgo = "moderado"
            elif "esfuerzo constante" in nivel_salud.lower() or "molestias frecuentes" in nivel_salud.lower():
                observaciones.append({
                    "categoria": "Salud percibida regular",
                    "hallazgo": "El paciente puede realizar actividades pero con esfuerzo constante y molestias frecuentes.",
                    "implicacion": "Existe capacidad funcional preservada pero con alto costo energético y sintomático.",
                    "recomendacion": "Optimizar estrategias de conservación de energía y técnicas de pacing para mejorar eficiencia funcional."
                })
                if nivel_riesgo == "bajo":
                    nivel_riesgo = "moderado"
        
        # --- 2. Análisis de la calidad del sueño (fatiga diurna) ---
        if frecuencia_sueno:
            if frecuencia_sueno.lower() == "siempre":
                observaciones.append({
                    "categoria": "Somnolencia diurna excesiva severa",
                    "hallazgo": "El paciente siempre se siente cansado o tiene dificultad para mantenerse despierto durante tareas rutinarias.",
                    "implicacion": "La somnolencia diurna excesiva puede indicar trastornos del sueño no diagnosticados (apnea del sueño, síndrome de piernas inquietas) o depresión. Aumenta el riesgo de accidentes y reduce la adherencia al tratamiento.",
                    "recomendacion": "Derivar a especialista en medicina del sueño. Evaluar Escala de Somnolencia de Epworth. Descartar apnea obstructiva del sueño."
                })
                nivel_riesgo = "alto"
            elif frecuencia_sueno.lower() == "frecuentemente":
                observaciones.append({
                    "categoria": "Somnolencia diurna excesiva moderada",
                    "hallazgo": "El paciente frecuentemente experimenta fatiga o somnolencia durante el día.",
                    "implicacion": "Sugiere higiene del sueño deficiente o trastorno del sueño subyacente. La fatiga crónica amplifica la percepción del dolor.",
                    "recomendacion": "Educar en higiene del sueño. Evaluar horas totales de sueño y calidad. Considerar Cuestionario de Calidad del Sueño de Pittsburgh (PSQI)."
                })
                if nivel_riesgo != "alto":
                    nivel_riesgo = "moderado"
        
        # --- 3. Análisis de la percepción del peso ---
        if opinion_peso:
            if "ganar mucho peso" in opinion_peso.lower():
                observaciones.append({
                    "categoria": "Deseo de ganancia significativa de peso",
                    "hallazgo": "El paciente desea ganar mucho peso.",
                    "implicacion": "Puede indicar desnutrición, pérdida de masa muscular (sarcopenia) o trastorno de la imagen corporal. La pérdida de peso no intencional en dolor crónico puede reflejar depresión o enfermedad sistémica.",
                    "recomendacion": "Evaluar IMC, composición corporal y estado nutricional. Descartar causas orgánicas de pérdida de peso. Considerar derivación a nutricionista."
                })
                if nivel_riesgo == "bajo":
                    nivel_riesgo = "moderado"
            elif "perder mucho peso" in opinion_peso.lower():
                observaciones.append({
                    "categoria": "Deseo de pérdida significativa de peso",
                    "hallazgo": "El paciente desea perder mucho peso.",
                    "implicacion": "Posible sobrepeso u obesidad. El exceso de peso aumenta la carga articular, inflamación sistémica y puede perpetuar el dolor musculoesquelético. IMC >30 se asocia con peor pronóstico en dolor crónico.",
                    "recomendacion": "Calcular IMC. Establecer plan de pérdida de peso gradual (0.5-1 kg/semana). Derivar a nutricionista. Programa de ejercicio adaptado de bajo impacto."
                })
                if nivel_riesgo == "bajo":
                    nivel_riesgo = "moderado"
        
        # --- 4. Análisis de hábitos alimenticios ---
        if consumo_comida_rapida:
            if "casi todos los dias" in consumo_comida_rapida.lower() or "casi todos los días" in consumo_comida_rapida.lower():
                observaciones.append({
                    "categoria": "Patrón alimenticio de alto riesgo",
                    "hallazgo": "El paciente consume comida rápida, bebidas azucaradas o alimentos ultraprocesados casi todos los días.",
                    "implicacion": "La dieta proinflamatoria (alta en azúcares refinados, grasas trans y sodio) aumenta la inflamación sistémica, empeora el dolor crónico y aumenta el riesgo cardiovascular y metabólico. Asociado con mayor riesgo de diabetes tipo 2 y síndrome metabólico.",
                    "recomendacion": "Educación nutricional urgente. Promover dieta antiinflamatoria (mediterránea). Derivación a nutricionista. Evaluar factores socioeconómicos que limiten acceso a alimentación saludable."
                })
                nivel_riesgo = "alto"
            elif "mas de la mitad" in consumo_comida_rapida.lower() or "más de la mitad" in consumo_comida_rapida.lower():
                observaciones.append({
                    "categoria": "Patrón alimenticio de riesgo moderado",
                    "hallazgo": "El paciente consume alimentos ultraprocesados más de la mitad de los días.",
                    "implicacion": "Patrón alimenticio subóptimo que contribuye a inflamación crónica de bajo grado y puede interferir con la recuperación.",
                    "recomendacion": "Consejería nutricional. Establecer metas graduales de reducción de alimentos procesados. Educar sobre relación dieta-inflamación-dolor."
                })
                if nivel_riesgo != "alto":
                    nivel_riesgo = "moderado"
        
        # --- Generar reporte final ---
        if not observaciones:
            return {
                'status': 'success',
                'title': 'Análisis de Determinantes Sociales de Salud',
                'nivel': 'Perfil favorable',
                'message': 'El paciente presenta un perfil de estilo de vida favorable sin factores de riesgo significativos identificados en las áreas evaluadas (percepción de salud, sueño, peso y alimentación).',
                'recommendation': 'Reforzar hábitos saludables actuales y mantener seguimiento preventivo.',
                'observaciones': []
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
            'message': f'Se identificaron {len(observaciones)} área(s) de preocupación relacionadas con el estilo de vida que pueden impactar el pronóstico y la respuesta al tratamiento:',
            'observaciones': observaciones,
            'note': 'Los determinantes sociales de salud (DSS) son factores no médicos que influyen significativamente en los resultados de salud. Abordar estos factores mediante intervenciones multidisciplinarias puede mejorar sustancialmente el pronóstico del paciente.'
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'title': 'Error de Evaluación',
            'message': f'Error al evaluar determinantes sociales de salud: {str(e)}'
        }
