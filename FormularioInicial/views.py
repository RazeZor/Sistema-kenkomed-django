from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from Login.models import formularioClinico, Clinico, Paciente,tiempo
from django.contrib import messages
import json



def FormularioInicial(request):
    # Verificar si el usuario tiene sesión activa como clínico
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)
        rut_clinico = request.session.get('rut_clinico')
        if not rut_clinico:
            messages.error(request, 'debe haber un inicio de sesion para estar aqui...')
            return redirect('login')

        try:
            clinico = Clinico.objects.get(rut=rut_clinico)
        except Clinico.DoesNotExist:
            messages.error(request, 'el clinico no esta en el sistema, intenta nuevamente...')
            return redirect('login')

            
        if request.method == 'POST':
            duracion_sesion_str = request.POST.get('duracion_sesion')

            try:
                horas, minutos, segundos = map(int, duracion_sesion_str.split(':'))
                duracion_sesion = timedelta(hours=horas, minutes=minutos, seconds=segundos)
                nuevo_tiempo = tiempo(duracion=duracion_sesion)
                nuevo_tiempo.save()
            except ValueError:
                messages.error(request, 'Formato de duración de sesión inválido.')
            rut = request.POST.get('rut')
            nombre = request.POST.get('nombre')
            apellido = request.POST.get('apellido')
            fechaNacimiento = request.POST.get('fechaNac')
            genero = request.POST.get('genero')
            contacto = request.POST.get('contact')
            trabajo = request.POST.get('trabajo')
            profesion = request.POST.get('profesion')
            cobertura_de_salud = request.POST.get('cobertura')
            LicenciaInicio = request.POST.get('fecha_inicio')
            LicenciaFin = request.POST.get('fecha_fin')
            LicenciaDias = request.POST.get('dias_licencia')
            

            # Validación de fecha
            try:
                fechaNacimiento = datetime.strptime(request.POST.get('fechaNac'), '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'la fecha de nacimiento tiene que tener el formato YYYY-MM-DD')
                return render(request, 'FormularioInicial.html')
            try:
                LicenciaInicio = datetime.strptime(request.POST.get('fecha_inicio'), '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'la fecha de inicio de licencia tiene que tener el formato YYYY-MM-DD')
                return render(request, 'FormularioInicial.html')

            errores = []
            #programacion negativa

            
            if not rut:
                errores.append('El campo RUT es obligatorio')
            if not nombre:
                errores.append('El campo nombre es obligatorio')
            if not apellido:
                errores.append('El campo apellido es obligatorio')
            if not fechaNacimiento:
                errores.append('El campo fecha de nacimiento es obligatorio.')
            if not genero:
                errores.append('El campo género es obligatorio.')
            if not contacto:
                errores.append('El campo contacto es obligatorio.')
            if not cobertura_de_salud:
                errores.append('El campo cobertura de salud es obligatorio.')
            if not trabajo:
                errores.append('El campo trabajo es obligatorio.')
            if not profesion:
                errores.append('El campo profesión es obligatorio.')
            if not LicenciaInicio:
                errores.append('El campo fecha de inicio de licencia es obligatorio.')
            if not LicenciaFin:
                errores.append('El campo fecha de fin de licencia es obligatorio.')
            if not LicenciaDias:
                errores.append('El campo dias de licencia es obligatorio.')
            

            if errores:
                for error in errores:
                    messages.error(request, error)
                return render(request, 'FormularioInicial.html')

            paciente, created = Paciente.objects.update_or_create(
                rut=rut,
                defaults={
                    'nombre': nombre,
                    'apellido': apellido,
                    'fechaNacimiento': fechaNacimiento,
                    'genero': genero,
                    'contacto': contacto,
                    'cobertura_de_salud': cobertura_de_salud,
                    'trabajo':trabajo,
                    'profesion':profesion,
                    'LicenciaInicio':LicenciaInicio,
                    'LicenciaFin':LicenciaFin,
                    'LicenciaDias':LicenciaDias
                    
            
                }
            )


            formulario = formularioClinico(
        paciente=paciente,
        clinico=clinico,
        fechaCreacion=datetime.now(),
        medicamentos = json.dumps(request.POST.getlist('medicamentos')),
        ## hasta aqui llega la parte de usuarios.
        
        
        ## pagina 2
        duracionDolor=request.POST.get('btnradio1'),
        caracteristicasDeDolor=json.dumps(request.POST.getlist('caracteristicas')),

        ## pagina 3 esquema
        ubicacionDolor = json.dumps(request.POST.getlist('ubicacionDolor')),
        dolorIntensidad= json.dumps(request.POST.getlist('intensidad')),
    
        
        ## pagina 4
        causaDolor=request.POST.get('causaDolor'),
        accidenteLaboral=json.dumps(request.POST.getlist('accidenteLaboral')),
        calidadAtencion=request.POST.get('calidadAtencion'),
        opinionProblemaEnfermeda=request.POST.get('diagnosis'),
        opinionCuraDolor=request.POST.get('cure'),
        #pagina 5
        TiposDeEnfermedades=json.dumps(request.POST.getlist('TiposDeEnfermedades')),

        #pagina 6
        IntensidadDolor=request.POST.get('IntensidadDolor'),
        preguntas1=json.dumps(request.POST.getlist('preguntas1')),
        
        nesesidadDeApoyo=request.POST.get('support'),
        #pagina 7
        actividades_afectadas = json.dumps(request.POST.getlist('actividades_afectadas')),
        parametros = json.dumps(request.POST.getlist('parametros')),
        
        #pagina8
        pregunta1_nivelDeSalud=request.POST.get('pregunta1_nivelDeSalud'),
        pregunta3_frecuencia_De_Suenio=request.POST.get('op3'),
        pregunta4_opinion_peso_actual=request.POST.get('pregunta4_opinion_peso_actual'),
        pregunta5_ConsumoComidaRapida=request.POST.get('op5'),
        
        #pagina 8.5 sueño
        hora_acostarse=request.POST.get('hora_acostarse'),
        tiempo_dormirse=request.POST.get('tiempo_dormirse'),
        hora_despertar=request.POST.get('hora_despertar'),
        hora_levantarse=request.POST.get('hora_levantarse'),
        despertares=request.POST.get('despertares'),

        #pagina 9
        pregunta6_PorcionesDeFrutas=request.POST.get('op6'),
        pregunta7_ejercicioDias=request.POST.get('op7'),
        pregunta8_minutosPorEjercicios=request.POST.get('op8'),
        #preguntas de salud mental
        
        proposito = request.POST.get('proposito'),
        red_de_apoyo = request.POST.get('red_de_apoyo'),
        placer_cosas = request.POST.get('placer_cosas'),
        deprimido = request.POST.get('deprimido'),
        ansioso = request.POST.get('ansioso'),
        preocupacion = request.POST.get('preocupacion'),

        #consumo de sustancias
        #nicotica
        NicotinaSiOno = request.POST.get('NicotinaSiOno'),
        condicionNicotina = request.POST.get('frecuenciaNicotina'),
        nicotinaPreocupacion = request.POST.get('preocupacionNicotina'),
        #cigarro
        AlcoholSiOno = request.POST.get('AlcoholSiOno'),
        condicionAlcohol = request.POST.get('frecuenciaAlcohol'),
        AlcoholPreocupacion = request.POST.get('preocupacionAlcohol'),
        #drogas
        drogasSiOno = request.POST.get('drogasSiOno'),
        condicionDrogas = request.POST.get('CantidadDrogras'),
        DrogasPreocupacion = request.POST.get('DrogasPreocupacion'),
        #marihuana
        marihuanaSiOno = request.POST.get('marihuanaSiOno'),
        condicionMarihuana = request.POST.get('frecuenciaMarihuana'),
        marihuanaPreocupacion = request.POST.get('marihuanaPreocupacion'),
        #preguntas de motivacion
        preguntas2=json.dumps(request.POST.getlist('preguntas2')),
        AreasMotivacion = json.dumps(request.POST.getlist('motivacion')),
        motivacion_Salud = request.POST.get('motivacion_Salud')

        )
            formulario.save()
            
            messages.success(request, 'Formulario guardado exitosamente.')
            return redirect('panel')

        return render(request, 'FormularioInicial.html')
    else:
        return redirect('login')
def CuerpoHumano(request):
    return render(request, 'CuerpoHumano.html')