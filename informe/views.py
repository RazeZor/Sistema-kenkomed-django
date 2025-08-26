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
        
        mensajeEVPER = Respuesta_evitativo_persistente(json.loads(formulario.parametros))
        
        MensajeNicotina = "no tiene" if formulario.nicotinaPreocupacion is None else formulario.nicotinaPreocupacion
        mensajeAcoholP = "no tiene" if formulario.AlcoholPreocupacion is None else formulario.AlcoholPreocupacion
        mensajeDrogasP = "no tiene" if formulario.DrogasPreocupacion is None else formulario.DrogasPreocupacion
        mensajeMarihuanaP = "no tiene" if formulario.marihuanaPreocupacion is None else formulario.marihuanaPreocupacion
        
        # Ubicación + Intensidad
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
            'encontrado': True
        }

    except formularioClinico.DoesNotExist:
        context = {
                'encontrado': False,
                'mensaje': "No se encontró el formulario clínico de este paciente."
            }

    return render(request, 'informe.html', context)

# funciones y algoritmo para las Respuesta de el informe 


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
