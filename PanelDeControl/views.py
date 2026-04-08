import json
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from Login.models import Paciente, formularioClinico,tiempo,Notas,Clinico
from django.http import HttpResponse, JsonResponse
from datetime import datetime, timedelta
import time 
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico

@requiere_clinico
def panel(request):
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)

        # 🔹 Buscar el clínico en la base de datos
        clinico = Clinico.objects.filter(nombre=nombre_clinico).first()
        profesion = clinico.profesion if clinico else "Sin profesión"


        # Obtener tiempos y calcular promedio
        tiempos = tiempo.objects.all()
        if tiempos.exists():
            total_duracion = sum((t.duracion for t in tiempos), timedelta())
            promedio_duracion = total_duracion / len(tiempos)
            horas, resto = divmod(promedio_duracion.total_seconds(), 3600)
            minutos, segundos = divmod(resto, 60)
            promedio_formateado = f"{int(horas):02}:{int(minutos):02}:{int(segundos):02}"
        else:
            promedio_formateado = "00:00:00"

        pacientes = Paciente.objects.all()
        numeroPaciente = pacientes.count()

        return render(request, 'panel.html', {
            'nombre_clinico': nombre_clinico,
            'profesion': profesion,
            'es_admin': es_admin,
            'promedio_formateado': promedio_formateado,
            'numeroPaciente': numeroPaciente
        })
    else:
        return redirect('login')
    
#def RenderizarDatosPaciente(request):
    #pacientes = Paciente.objects.all()
    #return render(request, 'panel.html', {'pacientes': pacientes})    

@requiere_clinico
def cerrar_sesion(request):
    # Elimina todos los datos de la sesión
    request.session.flush()

    # Borrar la cookie de sesión en el navegador (si existe nombre de cookie por defecto)
    response = redirect('login')
    session_cookie_name = None
    try:
        # Django por defecto usa settings.SESSION_COOKIE_NAME, pero importarlo aquí causaría ciclo.
        session_cookie_name = request.session.cookie_name
    except Exception:
        # fallback al nombre por defecto
        session_cookie_name = 'sessionid'

    response.delete_cookie(session_cookie_name)

    # Asegurar cabeceras no-cache también en esta respuesta
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


@requiere_clinico
def HistorialClinico(request):
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        rut_clinico = request.session.get('rut_clinico')
        es_admin = request.session.get('es_admin', False)
        paciente = None
        error = None
        nota_existente = None

        # Intentar obtener el objeto Clinico desde la sesión (si existe)
        clinico_obj = None
        if rut_clinico:
            clinico_obj = Clinico.objects.filter(rut=rut_clinico).first()

        rut = None
        nota_texto = None
        if request.method == 'POST':
            rut = request.POST.get('rutsito')
            nota_texto = request.POST.get('nota')
        elif request.method == 'GET':
            rut = request.GET.get('rut')
            
        # Revisamos si viene una redirección desde la creación de paciente    
        if 'temp_rut_historial' in request.session:
            rut = request.session['temp_rut_historial']
            del request.session['temp_rut_historial']

        if rut:
            try:
                # Filtrar según el tipo de usuario
                if es_admin:
                    paciente = Paciente.objects.get(rut=rut)
                else:
                    if not clinico_obj:
                        error = 'No se encontró el clínico en sesión. Inicia sesión nuevamente.'
                        raise Paciente.DoesNotExist()
                    paciente = Paciente.objects.get(rut=rut, clinico=clinico_obj)

                nota_existente, created = Notas.objects.get_or_create(paciente=paciente)

                if nota_texto:
                    nota_existente.notas = nota_texto
                    nota_existente.save()

            except Paciente.DoesNotExist:
                if not error:
                    error = "No se encontró ningún paciente con ese RUT o no tienes permisos para verlo."

        return render(request, 'HistorialClinicoPacientes.html', {
            'paciente': paciente,
            'error': error,
            'nota': nota_existente.notas if nota_existente else ''
        })
    else:
        return redirect('login')
@requiere_clinico
def VerInformePacientes(request):
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        
        nombre_clinico = request.session['nombre_clinico']
        rut = request.GET.get('rut', None)
        context = {'nombre_clinico': nombre_clinico}

        if rut:
            try:
                paciente = Paciente.objects.get(rut=rut)
                formulario = formularioClinico.objects.get(paciente=paciente)
                #escala Semaforo Integrada
                semaforo = json.loads(formulario.preguntas1)
                mensajeSemaforo = EscalaSemaforo(semaforo)
                opinionproblemaEnfermead = CreenciaDolor(formulario.opinionProblemaEnfermeda)
                #mensaje apoyo 
                mensajeApoyo = evaluar_necesidad_apoyo(formulario.nesesidadDeApoyo)
                
                #mensaje caracteristicas de dolor
                caracteristicasDolor = json.loads(formulario.caracteristicasDeDolor)
                MensajecaracteristicasDolor = Neuropaticas(caracteristicasDolor)

                #mensaje fibromialgia
                condicionesSalud1 = json.loads(formulario.TiposDeEnfermedades)
                MensajeCondicionesSalud = condicionesSalud(condicionesSalud1)

                # mensaje de evitacion 
                respuestas = formulario.parametros
                mensajeEVPER = Respuesta_evitativo_persistente(json.loads(respuestas)) 
                
                #preocupacion Consumo
                preocupacionNicotina = formulario.nicotinaPreocupacion
                MensajeNicotina = "no tiene" if preocupacionNicotina is None else preocupacionNicotina
                
                #preocupacion alchol
                preocupacionAlcohol = formulario.AlcoholPreocupacion
                mensajeAcoholP = "no tiene" if preocupacionAlcohol is None else preocupacionAlcohol
                
                #preocupacion drogas 
                preocupacionDrogas = formulario.DrogasPreocupacion
                mensajeDrogasP = "no tiene" if preocupacionDrogas is None else preocupacionDrogas
                
                #preocupacion marihuana
                preocupacionMarihuana = formulario.marihuanaPreocupacion
                mensajeMarihuanaP = "no tiene" if preocupacionMarihuana is None else preocupacionMarihuana
                
                #uso importante de JsonLoad, esta es la unica manera
                #que carguen bien las respuestas Json De el Atribuo JsonField de la base de Datos
                
                
                
                
                # el cuerpo humano Bien mostrado 
                ubicacionDolor = json.loads(formulario.ubicacionDolor)
                intensidadDolor = json.loads(formulario.dolorIntensidad)
                ubicacion_intensidad_list = ""
                min_len = min(len(ubicacionDolor), len(intensidadDolor))
                for i in range(min_len):
                    ubicacion = ubicacionDolor[i]
                    intensidad = intensidadDolor[i]
                    ubicacion_intensidad_list += f"<li><strong>{ubicacion}:</strong> {intensidad}</li>\n"
                if len(ubicacionDolor) != len(intensidadDolor):
                    ubicacion_intensidad_list += "<li><strong>Error:</strong> Las listas no coinciden en longitud</li>\n"

                
                
                # renderizar el informe 
                with open('informe/templates/informe.html', 'r', encoding='utf-8') as template_file:
                    informe_template = template_file.read()

                informe = informe_template.format(
                    paciente=paciente,
                    formulario=formulario,
                    mensajeApoyo=mensajeApoyo,
                    ubicacion_intensidad=ubicacion_intensidad_list,
                    mensajeSemaforo=mensajeSemaforo,
                    MensajecaracteristicasDolor=MensajecaracteristicasDolor,
                    MensajeCondicionesSalud=MensajeCondicionesSalud,
                    opinionproblemaEnfermead=opinionproblemaEnfermead,
                    mensajeEVPER=mensajeEVPER,
                    MensajeNicotina=MensajeNicotina,
                    mensajeAcoholP=mensajeAcoholP,
                    mensajeDrogasP=mensajeDrogasP,
                    mensajeMarihuanaP=mensajeMarihuanaP
                    
                )


                context['informe'] = informe
                context['encontrado'] = True

            except (Paciente.DoesNotExist, formularioClinico.DoesNotExist):
                context['encontrado'] = False
                context['mensaje'] = "No se encontró el paciente o su formulario clínico"

        return render(request, 'FichaPacientes.html', context)
    else:
        return redirect('login')



# funciones y algoritmo para las Respuesta de el informe 

def evaluar_necesidad_apoyo(apoyo):
    if apoyo == 'si':
        return (
            '<div style="'
            'background: linear-gradient(135deg, #fef7f7 0%, #fdf2f2 100%); '
            'color: #7f1d1d; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #ef4444; '
            'box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #ef4444; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">!</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #7f1d1d; '
            'line-height: 1.4;'
            '">Apoyo Psicológico Requerido</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #991b1b;'
            '">El paciente solicita apoyo para ansiedad o depresión. Se sugiere derivar a un especialista (psicólogo, psiquiatra). Se recomienda al clínico usar Formulario PHQ-9.</p>'
            '</div>'
            '</div>'
            '</div>'
        )
    return ''

def EscalaSemaforo(preguntas1):
    score = 0
    RESPUESTA = 'si'
    MODERADO = 'moderado'
    MUCHO = 'mucho'
    EXTREMO = 'extremo'
    
    for preguntas in preguntas1:
        if preguntas == RESPUESTA:
            score += 1
        if preguntas.strip().lower() in [MODERADO, MUCHO, EXTREMO]:
            score += 1
    
    if score <= 3:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); '
            'color: #14532d; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #22c55e; '
            'box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #22c55e; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">✓</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #14532d; '
            'line-height: 1.4;'
            '">Riesgo Bajo - Diagnóstico Favorable</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #166534;'
            '">Según la Escala Screening Semáforo, el paciente presenta riesgo bajo. Se recomienda educar y tranquilizar al paciente sobre el pronóstico favorable.</p>'
            '</div>'
            '</div>'
            '</div>'
        )
    elif score >= 4 and score <= 7:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); '
            'color: #92400e; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #f59e0b; '
            'box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #f59e0b; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">⚠</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #92400e; '
            'line-height: 1.4;'
            '">Riesgo Medio - Evaluación Adicional</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #a16207;'
            '">Según la Escala Screening Semáforo, el paciente presenta riesgo medio. Evaluar si necesitará apoyo de otro profesional.</p>'
            '</div>'
            '</div>'
            '</div>'
        )
    elif score >= 8:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #fef7f7 0%, #fdf2f2 100%); '
            'color: #7f1d1d; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #ef4444; '
            'box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #ef4444; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">!</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #7f1d1d; '
            'line-height: 1.4;'
            '">Riesgo Alto - Tratamiento Interdisciplinario</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #991b1b;'
            '">Según la Escala Screening Semáforo, el paciente presenta riesgo alto. Se recomienda tratamiento interdisciplinario.</p>'
            '</div>'
            '</div>'
            '</div>'
        )

def Neuropaticas(caracteristicasDolor):
    for caracteristicas in caracteristicasDolor:
        if caracteristicas in ["ardiente", "corriente", "adormecimiento", "Hormigueo"]:
            return (
                '<div style="'
                'background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); '
                'color: #0c4a6e; '
                'padding: 20px; '
                'border-radius: 12px; '
                'border-left: 4px solid #0ea5e9; '
                'box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1); '
                'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
                'margin: 16px 0;'
                '">'
                '<div style="display: flex; align-items: flex-start; gap: 12px;">'
                '<div style="'
                'width: 24px; '
                'height: 24px; '
                'background: #0ea5e9; '
                'border-radius: 50%; '
                'display: flex; '
                'align-items: center; '
                'justify-content: center; '
                'color: white; '
                'font-size: 14px; '
                'font-weight: 600; '
                'flex-shrink: 0; '
                'margin-top: 2px;'
                '">i</div>'
                '<div>'
                '<h6 style="'
                'margin: 0 0 8px 0; '
                'font-size: 16px; '
                'font-weight: 600; '
                'color: #0c4a6e; '
                'line-height: 1.4;'
                '">Dolor Neuropático Detectado</h6>'
                '<p style="'
                'margin: 0; '
                'font-size: 14px; '
                'line-height: 1.5; '
                'color: #075985;'
                '">El paciente presenta características de dolor neuropático. Se recomienda al clínico usar la Escala DN4.</p>'
                '</div>'
                '</div>'
                '</div>'
            )
    return ''

def condicionesSalud(condicionesSalud):
    mensajes = []
    
    recomendaciones = {
        "Fibromialgia": "Fibromialgia detectada - Se recomienda uso de formulario específico para Fibromialgia",
        "Hormigueos o adormecimiento": "Síntomas neurológicos - Se recomienda uso de formulario de dolor neuropático",
        "diabetes": "Diabetes presente - Se recomienda uso de formulario de dolor neuropático",
        "Ansiedad": "Ansiedad detectada - Se recomienda uso de formulario abreviado de Depresión",
        "Depresion": "Depresión detectada - Se recomienda uso de formulario abreviado de Depresión"
    }
    
    for condicion in condicionesSalud:
        if condicion in recomendaciones:
            mensajes.append(f'<li style="margin: 8px 0; color: #075985;">{recomendaciones[condicion]}</li>')
    
    if mensajes:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); '
            'color: #0c4a6e; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #0ea5e9; '
            'box-shadow: 0 2px 8px rgba(14, 165, 233, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #0ea5e9; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">📋</div>'
            '<div style="width: 100%;">'
            '<h6 style="'
            'margin: 0 0 12px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #0c4a6e; '
            'line-height: 1.4;'
            '">Condiciones de Salud Relevantes</h6>'
            '<ul style="'
            'margin: 0; '
            'padding-left: 20px; '
            'font-size: 14px; '
            'line-height: 1.5;'
            '">' +
            "".join(mensajes) +
            '</ul>'
            '</div>'
            '</div>'
            '</div>'
        )
    
    return ""

def CreenciaDolor(CreenciaDolor):
    if CreenciaDolor == 'si':
        return (
            '<div style="'
            'background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); '
            'color: #92400e; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #f59e0b; '
            'box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #f59e0b; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">?</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #92400e; '
            'line-height: 1.4;'
            '">Creencias sobre el Dolor</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #a16207;'
            '">El paciente cree que tiene un dolor no diagnosticado. Se sugiere uso de Pain Catastrophizing Scale (PCS).</p>'
            '</div>'
            '</div>'
            '</div>'
        )
    return ''

def Respuesta_evitativo_persistente(respuestas):
    EVITATIVAS = "evitativo"
    PERSISTENTES = "persistente"
    evitativo = 0
    persistente = 0
    
    for respuesta in respuestas:
        if respuesta.strip().lower() == EVITATIVAS:
            evitativo += 1
        elif respuesta.strip().lower() == PERSISTENTES:
            persistente += 1
    
    if evitativo > persistente:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); '
            'color: #92400e; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #f59e0b; '
            'box-shadow: 0 2px 8px rgba(245, 158, 11, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #f59e0b; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">⏸</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #92400e; '
            'line-height: 1.4;'
            '">Conducta de Evitación</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #a16207;'
            '">El paciente presenta una conducta predominantemente evitativa ante el dolor.</p>'
            '</div>'
            '</div>'
            '</div>'
        )
    elif persistente > evitativo:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #fef7f7 0%, #fdf2f2 100%); '
            'color: #7f1d1d; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #ef4444; '
            'box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #ef4444; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">▶</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #7f1d1d; '
            'line-height: 1.4;'
            '">Conducta de Persistencia</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #991b1b;'
            '">El paciente presenta una conducta predominantemente persistente ante el dolor.</p>'
            '</div>'
            '</div>'
            '</div>'
        )
    else:
        return (
            '<div style="'
            'background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); '
            'color: #14532d; '
            'padding: 20px; '
            'border-radius: 12px; '
            'border-left: 4px solid #22c55e; '
            'box-shadow: 0 2px 8px rgba(34, 197, 94, 0.1); '
            'font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif; '
            'margin: 16px 0;'
            '">'
            '<div style="display: flex; align-items: flex-start; gap: 12px;">'
            '<div style="'
            'width: 24px; '
            'height: 24px; '
            'background: #22c55e; '
            'border-radius: 50%; '
            'display: flex; '
            'align-items: center; '
            'justify-content: center; '
            'color: white; '
            'font-size: 14px; '
            'font-weight: 600; '
            'flex-shrink: 0; '
            'margin-top: 2px;'
            '">⚖</div>'
            '<div>'
            '<h6 style="'
            'margin: 0 0 8px 0; '
            'font-size: 16px; '
            'font-weight: 600; '
            'color: #14532d; '
            'line-height: 1.4;'
            '">Conducta Equilibrada</h6>'
            '<p style="'
            'margin: 0; '
            'font-size: 14px; '
            'line-height: 1.5; '
            'color: #166534;'
            '">El paciente presenta una conducta equilibrada ante el dolor.</p>'
            '</div>'
            '</div>'
            '</div>'
        )


@require_http_methods(["POST"])
@csrf_exempt
def clear_session_message(request):
    """Vista para limpiar el mensaje de la sesión después de mostrarlo."""
    if 'show_success_message' in request.session:
        del request.session['show_success_message']
        request.session.modified = True
    return JsonResponse({'status': 'success'})


@requiere_clinico
def estadisticas(request):
    """Vista para mostrar estadísticas y análisis de datos clínicos"""
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    nombre_clinico = request.session['nombre_clinico']
    es_admin = request.session.get('es_admin', False)
    rut_clinico = request.session.get('rut_clinico')

    # Filtrar pacientes según si es admin o clínico normal
    if es_admin:
        pacientes = Paciente.objects.all()
        formularios = formularioClinico.objects.all()
    else:
        clinico_obj = Clinico.objects.filter(rut=rut_clinico).first()
        if not clinico_obj:
            return redirect('login')
        pacientes = Paciente.objects.filter(clinico=clinico_obj)
        formularios = formularioClinico.objects.filter(paciente__clinico=clinico_obj)

    # === ESTADÍSTICAS GENERALES ===
    total_pacientes = pacientes.count()
    total_formularios = formularios.count()
    
    # Distribución por género
    distribucion_genero = {
        'labels': [],
        'data': []
    }
    generos = pacientes.values('genero').distinct()
    for genero in generos:
        if genero['genero']:
            count = pacientes.filter(genero=genero['genero']).count()
            distribucion_genero['labels'].append(genero['genero'])
            distribucion_genero['data'].append(count)
    
    # === ANÁLISIS DE DOLOR ===
    # Ubicaciones de dolor más comunes
    ubicaciones_dolor = {}
    for form in formularios:
        if form.ubicacionDolor:
            try:
                ubicaciones = json.loads(form.ubicacionDolor)
                for ubicacion in ubicaciones:
                    ubicaciones_dolor[ubicacion] = ubicaciones_dolor.get(ubicacion, 0) + 1
            except:
                pass
    
    # Top 10 ubicaciones
    top_ubicaciones = dict(sorted(ubicaciones_dolor.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Intensidad promedio del dolor
    intensidades = []
    for form in formularios:
        if form.dolorIntensidad:
            try:
                intensidad_list = json.loads(form.dolorIntensidad)
                for intensidad in intensidad_list:
                    try:
                        intensidades.append(int(intensidad))
                    except:
                        pass
            except:
                pass
    
    intensidad_promedio = sum(intensidades) / len(intensidades) if intensidades else 0
    
    # Distribución de intensidad del dolor
    distribucion_intensidad = {str(i): 0 for i in range(1, 11)}
    for intensidad in intensidades:
        if 1 <= intensidad <= 10:
            distribucion_intensidad[str(intensidad)] += 1
    
    # === CONDICIONES DE SALUD ===
    condiciones_salud = {}
    for form in formularios:
        if form.TiposDeEnfermedades:
            try:
                condiciones = json.loads(form.TiposDeEnfermedades)
                for condicion in condiciones:
                    condiciones_salud[condicion] = condiciones_salud.get(condicion, 0) + 1
            except:
                pass
    
    # Top 10 condiciones
    top_condiciones = dict(sorted(condiciones_salud.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # === ANÁLISIS DE ESTILO DE VIDA ===
    # Nivel de salud percibido
    niveles_salud = {}
    for form in formularios:
        if form.pregunta1_nivelDeSalud:
            # Simplificar las respuestas
            if "muy afectada" in form.pregunta1_nivelDeSalud.lower():
                nivel = "Muy malo"
            elif "muchas molestias" in form.pregunta1_nivelDeSalud.lower():
                nivel = "Malo"
            elif "esfuerzo constante" in form.pregunta1_nivelDeSalud.lower():
                nivel = "Regular"
            elif "bien la mayor parte" in form.pregunta1_nivelDeSalud.lower():
                nivel = "Bien"
            elif "saludable" in form.pregunta1_nivelDeSalud.lower():
                nivel = "Muy bien"
            else:
                nivel = "No especificado"
            
            niveles_salud[nivel] = niveles_salud.get(nivel, 0) + 1
    
    # Consumo de comida rápida
    consumo_comida_rapida = {}
    for form in formularios:
        if form.pregunta5_ConsumoComidaRapida:
            consumo_comida_rapida[form.pregunta5_ConsumoComidaRapida] = consumo_comida_rapida.get(form.pregunta5_ConsumoComidaRapida, 0) + 1
    
    # === ANÁLISIS DE SUEÑO ===
    problemas_sueno = {
        'Hora acostarse tarde': 0,
        'Dificultad para dormir': 0,
        'Despertar temprano': 0,
        'Tiempo en levantarse': 0,
        'Despertares nocturnos': 0
    }
    
    for form in formularios:
        if form.hora_acostarse == "despues_0000":
            problemas_sueno['Hora acostarse tarde'] += 1
        if form.tiempo_dormirse in ["30_60", "mas_60"]:
            problemas_sueno['Dificultad para dormir'] += 1
        if form.hora_despertar == "antes_0500":
            problemas_sueno['Despertar temprano'] += 1
        if form.hora_levantarse in ["30_60", "mas_60"]:
            problemas_sueno['Tiempo en levantarse'] += 1
        if form.despertares in ["2_3", "mas_3"]:
            problemas_sueno['Despertares nocturnos'] += 1
    
    # === PATRÓN EVITATIVO/PERSISTENTE ===
    patrones_conducta = {'Evitativo': 0, 'Persistente': 0, 'Equilibrado': 0}
    for form in formularios:
        if form.parametros:
            try:
                respuestas = json.loads(form.parametros)
                evitativo = sum(1 for r in respuestas if r.strip().lower() == 'evitativo')
                persistente = sum(1 for r in respuestas if r.strip().lower() == 'persistente')
                
                if evitativo > persistente:
                    patrones_conducta['Evitativo'] += 1
                elif persistente > evitativo:
                    patrones_conducta['Persistente'] += 1
                else:
                    patrones_conducta['Equilibrado'] += 1
            except:
                pass
    
    # === TENDENCIAS TEMPORALES ===
    # Formularios por mes (últimos 6 meses)
    hoy = datetime.now()
    pacientes_por_mes = {}
    for i in range(6):
        mes = (hoy - timedelta(days=30*i)).strftime('%B %Y')
        pacientes_por_mes[mes] = 0
    
    for formulario in formularios:
        if formulario.fechaCreacion:
            mes = formulario.fechaCreacion.strftime('%B %Y')
            if mes in pacientes_por_mes:
                pacientes_por_mes[mes] += 1
    
    context = {
        'nombre_clinico': nombre_clinico,
        'es_admin': es_admin,
        'total_pacientes': total_pacientes,
        'total_formularios': total_formularios,
        'distribucion_genero': json.dumps(distribucion_genero),
        'top_ubicaciones': json.dumps({'labels': list(top_ubicaciones.keys()), 'data': list(top_ubicaciones.values())}),
        'intensidad_promedio': round(intensidad_promedio, 1),
        'distribucion_intensidad': json.dumps({'labels': list(distribucion_intensidad.keys()), 'data': list(distribucion_intensidad.values())}),
        'top_condiciones': json.dumps({'labels': list(top_condiciones.keys()), 'data': list(top_condiciones.values())}),
        'niveles_salud': json.dumps({'labels': list(niveles_salud.keys()), 'data': list(niveles_salud.values())}),
        'consumo_comida_rapida': json.dumps({'labels': list(consumo_comida_rapida.keys()), 'data': list(consumo_comida_rapida.values())}),
        'problemas_sueno': json.dumps({'labels': list(problemas_sueno.keys()), 'data': list(problemas_sueno.values())}),
        'patrones_conducta': json.dumps({'labels': list(patrones_conducta.keys()), 'data': list(patrones_conducta.values())}),
        'pacientes_por_mes': json.dumps({'labels': list(reversed(list(pacientes_por_mes.keys()))), 'data': list(reversed(list(pacientes_por_mes.values())))}),
    }
    
    return render(request, 'estadisticas.html', context)
