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
        
        # hora_acostarse = models.TextField(null=True,blank=True)
        #tiempo_dormirse = models.TextField(null=True,blank=True)
        #hora_despertar = models.TextField(null=True,blank=True)
        #hora_levantarse = models.TextField(null=True,blank=True)
        #despertares = models.TextField(null=True,blank=True)
        mensajeEVPER = Respuesta_evitativo_persistente(json.loads(formulario.parametros))
        
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
    Devuelve un bloque HTML con observaciones para el kinesiólogo.
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
            return (
                '<div style="background-color: #d4edda; color: #155724; padding: 15px; '
                'border-radius: 5px; border: 1px solid #c3e6cb;">'
                '<label>El paciente no presenta dificultades relevantes para dormir.</label>'
                '</div>'
            )
        else:
            lista = "".join([f"<li>{m}</li>" for m in mensajes])
            return (
                '<div style="background-color: #fff3cd; color: #856404; padding: 15px; '
                'border-radius: 5px; border: 1px solid #ffeeba;">'
                '<label><strong>Observaciones sobre el sueño:</strong></label>'
                f'<ul>{lista}</ul>'
                '</div>'
            )

    except Exception as e:
        return (
            '<div style="background-color: #e2e3e5; color: #383d41; padding: 15px; '
            'border-radius: 5px; border: 1px solid #d6d8db;">'
            f'<label>Error al procesar el formulario de sueño: {str(e)}</label>'
            '</div>'
        )





000

def Neuropaticas(caracteristicasDolor):
    for caracteristicas in caracteristicasDolor:
        if caracteristicas == "ardiente" or caracteristicas == "corriente" or caracteristicas == "adormecimiento" or caracteristicas == "Hormigueo":
            return (
                '<div style="background-color: #fff3cd; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">'
                '<label>El paciente tiene un dolor neuropático se recomienda al Clinico Usar la Escala DN4 </label>'
                '</div>'
            )
    return ('')


def condicionesSalud(condicionesSalud):
    mensajes = []
    
    recomendaciones = {
        "Fibromialgia": "El paciente tiene una enfermedad de Fibromialgia, se recomienda uso de formulario para Fibromialgia",
        "Hormigueos o adormecimiento": "El paciente tiene una enfermedad de Hormigueos o adormecimiento, se recomienda uso de formulario de dolor neuropático",
        "diabetes": "El paciente tiene una enfermedad de diabetes, se recomienda uso de formulario de dolor neuropático",
        "Ansiedad": "El paciente tiene una enfermedad de Ansiedad, se recomienda uso de formulario abreviado de Depresión",
        "Depresion": "El paciente tiene una enfermedad de Depresión, se recomienda uso de formulario abreviado de Depresión"
    }
    
    for condicion in condicionesSalud:
        if condicion in recomendaciones:
            mensajes.append(f"<label>{recomendaciones[condicion]}</label>")
    
    if mensajes:
        return (
            '<div style="background-color: #fff3cd; color: #155724; padding: 15px; '
            'border-radius: 5px; border: 1px solid #c3e6cb;">' +
            "<br>".join(mensajes) +
            "</div>"
        )
    
    return ""

def CreenciaDolor(CreenciaDolor):
    if (CreenciaDolor == 'si'):
        return (
                '<div style="background-color: #fff3cd; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">'
                '<label>El paciente cree que tiene un dolor no diagnosticado, Se suguiere uso de Pain Catastrophizing Scale (PCS) </label>'
                '</div>'
            )
    return ('')


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
        return ('<div style="background-color: #fff3cd; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">'
                '<label>Paciente tiene una conducta de evitacion</label>'
                '</div>')
    elif persistente > evitativo:
        return  ('<div style="background-color: #f8d7da; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">'
                '<label>Paciente tiene una conducta de persistencia</label>'
                '</div>')
    else:
        return  ('<div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb;">'
                '<label>Paciente tiene una conducta equilibrada</label>'
                '</div>')
