from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from Login.models import formularioClinico, Clinico, Paciente, tiempo
from django.contrib import messages
import json


# --------------------------
# Funciones auxiliares en español
# --------------------------


def obtener_clinico_desde_sesion(request):
    """Obtiene el objeto Clinico desde la sesión.
    Retorna (clinico, es_admin) o (None, False) si hay un problema.
    Agrega mensajes y no hace redirect aquí (lo hace la view).
    """
    if 'nombre_clinico' not in request.session:
        return (None, False)

    es_admin = request.session.get('es_admin', False)
    rut_clinico = request.session.get('rut_clinico')
    if not rut_clinico:
        messages.error(request, 'debe haber un inicio de sesion para estar aqui...')
        return (None, es_admin)

    try:
        clinico = Clinico.objects.get(rut=rut_clinico)
        return (clinico, es_admin)
    except Clinico.DoesNotExist:
        messages.error(request, 'el clinico no esta en el sistema, intenta nuevamente...')
        return (None, es_admin)


def parsear_duracion_sesion(duracion_str):
    """Convierte una cadena HH:MM:SS a un objeto tiempo 'tiempo' del modelo.
    Retorna la instancia guardada o None si el formato es inválido.
    """
    if not duracion_str:
        return None
    try:
        horas, minutos, segundos = map(int, duracion_str.split(':'))
        duracion_sesion = timedelta(hours=horas, minutes=minutos, seconds=segundos)
        nuevo_tiempo = tiempo(duracion=duracion_sesion)
        nuevo_tiempo.save()
        return nuevo_tiempo
    except Exception:
        return None


def parsear_fecha_campo(fecha_str, campo_nombre, request):
    """Parsea una fecha en formato YYYY-MM-DD. Si falla, agrega mensaje y retorna None."""
    try:
        return datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except Exception:
        messages.error(request, f'El campo {campo_nombre} debe tener formato YYYY-MM-DD')
        return None


def validar_campos_obligatorios(datos):
    """Recibe un dict con valores y devuelve una lista de errores por campos vacíos."""
    errores = []
    required = [
        ('rut', 'El campo RUT es obligatorio'),
        ('nombre', 'El campo nombre es obligatorio'),
        ('apellido', 'El campo apellido es obligatorio'),
        ('fechaNacimiento', 'El campo fecha de nacimiento es obligatorio.'),
        ('genero', 'El campo género es obligatorio.'),
        ('contacto', 'El campo contacto es obligatorio.'),
        ('cobertura_de_salud', 'El campo cobertura de salud es obligatorio.'),
        ('trabajo', 'El campo trabajo es obligatorio.'),
        ('profesion', 'El campo profesión es obligatorio.'),
        ('LicenciaInicio', 'El campo fecha de inicio de licencia es obligatorio.'),
        ('LicenciaFin', 'El campo fecha de fin de licencia es obligatorio.'),
        ('LicenciaDias', 'El campo dias de licencia es obligatorio.'),
    ]
    for campo, mensaje in required:
        if not datos.get(campo):
            errores.append(mensaje)
    return errores


def crear_o_actualizar_paciente(rut, defaults, clinico=None):
    """Crea o actualiza el paciente. Si se crea, asigna el clínico (si existe el campo)."""
    paciente, created = Paciente.objects.update_or_create(rut=rut, defaults=defaults)
    if created and clinico:
        try:
            paciente.clinico = clinico
            paciente.save()
        except Exception:
            # Si no existe el campo clinico o falla, no interrumpimos el flujo
            pass
    return paciente, created


def construir_formulario_desde_post(request, paciente, clinico, tiempo_obj):
    """Construye y guarda el objeto formularioClinico a partir de request.POST y objetos dados."""
    form = formularioClinico(
        paciente=paciente,
        clinico=clinico,
        fechaCreacion=datetime.now(),
        medicamentos=json.dumps(request.POST.getlist('medicamentos')),

        # pagina 2
        duracionDolor=request.POST.get('btnradio1'),
        caracteristicasDeDolor=json.dumps(request.POST.getlist('caracteristicas')),

        # pagina 3 esquema
        ubicacionDolor=json.dumps(request.POST.getlist('ubicacionDolor')),
        dolorIntensidad=json.dumps(request.POST.getlist('intensidad')),

        # pagina 4
        causaDolor=request.POST.get('causaDolor'),
        accidenteLaboral=json.dumps(request.POST.getlist('accidenteLaboral')),
        calidadAtencion=request.POST.get('calidadAtencion'),
        opinionProblemaEnfermeda=request.POST.get('diagnosis'),
        opinionCuraDolor=request.POST.get('cure'),

        # pagina 5
        TiposDeEnfermedades=json.dumps(request.POST.getlist('TiposDeEnfermedades')),

        # pagina 7
        actividades_afectadas=json.dumps(request.POST.getlist('actividades_afectadas')),
        parametros=json.dumps(request.POST.getlist('parametros')),

        # pagina8
        pregunta1_nivelDeSalud=request.POST.get('pregunta1_nivelDeSalud'),
        pregunta3_frecuencia_De_Suenio=request.POST.get('op3'),
        pregunta4_opinion_peso_actual=request.POST.get('pregunta4_opinion_peso_actual'),
        pregunta5_ConsumoComidaRapida=request.POST.get('op5'),

        # pagina 8.5 sueño
        hora_acostarse=request.POST.get('hora_acostarse'),
        tiempo_dormirse=request.POST.get('tiempo_dormirse'),
        hora_despertar=request.POST.get('hora_despertar'),
        hora_levantarse=request.POST.get('hora_levantarse'),
        despertares=request.POST.get('despertares'),

        # pagina 9
        pregunta6_PorcionesDeFrutas=request.POST.get('op6'),
        pregunta7_ejercicioDias=request.POST.get('op7'),
        pregunta8_minutosPorEjercicios=request.POST.get('op8'),

        # salud mental y motivación
        proposito=request.POST.get('proposito'),
        red_de_apoyo=request.POST.get('red_de_apoyo'),
        placer_cosas=request.POST.get('placer_cosas'),
        deprimido=request.POST.get('deprimido'),
        ansioso=request.POST.get('ansioso'),
        preocupacion=request.POST.get('preocupacion'),

        # consumo sustancias
        NicotinaSiOno=request.POST.get('NicotinaSiOno'),
        condicionNicotina=request.POST.get('frecuenciaNicotina'),
        nicotinaPreocupacion=request.POST.get('preocupacionNicotina'),
        AlcoholSiOno=request.POST.get('AlcoholSiOno'),
        condicionAlcohol=request.POST.get('frecuenciaAlcohol'),
        AlcoholPreocupacion=request.POST.get('preocupacionAlcohol'),
        drogasSiOno=request.POST.get('drogasSiOno'),
        condicionDrogas=request.POST.get('CantidadDrogras'),
        DrogasPreocupacion=request.POST.get('DrogasPreocupacion'),
        marihuanaSiOno=request.POST.get('marihuanaSiOno'),
        condicionMarihuana=request.POST.get('frecuenciaMarihuana'),
        marihuanaPreocupacion=request.POST.get('marihuanaPreocupacion'),

        # preguntas de motivación
        preguntas2=json.dumps(request.POST.getlist('preguntas2')),
        AreasMotivacion=json.dumps(request.POST.getlist('motivacion')),
        motivacion_Salud=request.POST.get('motivacion_Salud'),
    )

    form.save()
    return form


# --------------------------
# Vista principal
def FormularioInicial(request):
    # Verificar si el usuario tiene sesión activa como clínico
    if 'nombre_clinico' not in request.session:
        return redirect('login')

    nombre_clinico = request.session['nombre_clinico']
    clinico, es_admin = obtener_clinico_desde_sesion(request)
    if not clinico and not es_admin:
        return redirect('login')

    if request.method == 'POST':
        # Parsear duración de sesión y crear registro tiempo
        duracion_sesion_str = request.POST.get('duracion_sesion')
        nuevo_tiempo = parsear_duracion_sesion(duracion_sesion_str)
        if duracion_sesion_str and not nuevo_tiempo:
            messages.error(request, 'Formato de duración de sesión inválido.')

        rut = request.POST.get('rut')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fechaNacimiento_raw = request.POST.get('fechaNac')
        genero = request.POST.get('genero')
        contacto = request.POST.get('contact')
        trabajo = request.POST.get('trabajo')
        profesion = request.POST.get('profesion')
        cobertura_de_salud = request.POST.get('cobertura')
        LicenciaInicio_raw = request.POST.get('fecha_inicio')
        LicenciaFin_raw = request.POST.get('fecha_fin')
        LicenciaDias = request.POST.get('dias_licencia')

        # Parseo de fechas con mensajes en caso de error
        fechaNacimiento = parsear_fecha_campo(fechaNacimiento_raw, 'fecha de nacimiento', request)
        if fechaNacimiento is None:
            return render(request, 'FormularioInicial.html')

        LicenciaInicio = parsear_fecha_campo(LicenciaInicio_raw, 'fecha de inicio de licencia', request)
        if LicenciaInicio is None:
            return render(request, 'FormularioInicial.html')

        datos_para_validar = {
            'rut': rut,
            'nombre': nombre,
            'apellido': apellido,
            'fechaNacimiento': fechaNacimiento,
            'genero': genero,
            'contacto': contacto,
            'cobertura_de_salud': cobertura_de_salud,
            'trabajo': trabajo,
            'profesion': profesion,
            'LicenciaInicio': LicenciaInicio,
            'LicenciaFin': LicenciaFin_raw,
            'LicenciaDias': LicenciaDias,
        }

        errores = validar_campos_obligatorios(datos_para_validar)
        if errores:
            for e in errores:
                messages.error(request, e)
            return render(request, 'FormularioInicial.html')

        # Crear/actualizar paciente
        defaults = {
            'nombre': nombre,
            'apellido': apellido,
            'fechaNacimiento': fechaNacimiento,
            'genero': genero,
            'contacto': contacto,
            'cobertura_de_salud': cobertura_de_salud,
            'trabajo': trabajo,
            'profesion': profesion,
            'LicenciaInicio': LicenciaInicio,
            'LicenciaFin': LicenciaFin_raw,
            'LicenciaDias': LicenciaDias,
        }

        paciente, created = crear_o_actualizar_paciente(rut, defaults, clinico=clinico)

        # Construir y guardar formulario Clínico con todos los campos
        construir_formulario_desde_post(request, paciente, clinico, nuevo_tiempo)
        
        # Guardar mensaje en la sesión
        request.session['show_success_message'] = 'Paciente guardado exitosamente.'
        return redirect('panel')

    return render(request, 'FormularioInicial.html')
