from datetime import datetime, timedelta
import re
from django.shortcuts import render, redirect, get_object_or_404
from Login.models import formularioClinico, Clinico, Paciente, tiempo
from FormularioInicial.models import TokenFormulario
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.urls import reverse
import json
import qrcode
from io import BytesIO
import base64

def obtener_clinico_desde_sesion(request):
    """Obtiene el objeto Clinico desde la sesión.
    Retorna (clinico, es_admin) o (None, False) si hay un problema.
    Agrega mensajes y no hace redirect aqui (lo hace la view).
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

def validar_rut(rut):
    """Valida un RUT chileno con o sin puntos y con guion."""
    # Eliminar puntos y guiones, y convertir a mayúsculas
    rut = str(rut).replace('.', '').replace('-', '').upper()
    
    # Verificar longitud mínima
    if len(rut) < 2:
        return False
    
    # Separar números y dígito verificador
    cuerpo = rut[:-1]
    dv = rut[-1]
    
    # Validar que el cuerpo sean solo dígitos
    if not cuerpo.isdigit():
        return False
    
    # Validar dígito verificador
    suma = 0
    multiplo = 2
    
    # Calcular dígito verificador esperado
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo += 1
        if multiplo == 8:
            multiplo = 2
    
    resto = suma % 11
    dv_esperado = str(11 - resto)
    
    # Casos especiales
    if dv_esperado == '11':
        dv_esperado = '0'
    elif dv_esperado == '10':
        dv_esperado = 'K'
    
    return dv == dv_esperado

def validar_telefono(telefono):
    """Valida que el teléfono tenga el formato correcto."""
    if not telefono:
        return False
        
    # Eliminar espacios, paréntesis y guiones
    telefono_limpio = re.sub(r'[\s()+-]', '', str(telefono))
    
    # Validar que solo contenga dígitos
    if not telefono_limpio.isdigit():
        return False
    
    # Validar longitud (mínimo 8 dígitos, máximo 12 para incluir códigos de país)
    if len(telefono_limpio) < 8 or len(telefono_limpio) > 12:
        return False
    
    return True

def validar_campos_obligatorios(datos):
    """Recibe un dict con valores y devuelve una lista de errores por campos vacíos o inválidos."""
    errores = []
    
    # Validar RUT
    rut = datos.get('rut', '')
    if not rut:
        errores.append('El campo RUT es obligatorio')
    elif not validar_rut(rut):
        errores.append('El RUT ingresado no es válido')
    elif Paciente.objects.filter(rut=rut).exists():
        errores.append('El RUT ya existe en el sistema')
    
    # Validar nombre y apellido
    nombre = datos.get('nombre', '').strip()
    if not nombre:
        errores.append('El campo nombre es obligatorio')
    elif not nombre.replace(' ', '').isalpha():
        errores.append('El nombre solo puede contener letras y espacios')
    
    apellido = datos.get('apellido', '').strip()
    if not apellido:
        errores.append('El campo apellido es obligatorio')
    elif not apellido.replace(' ', '').isalpha():
        errores.append('El apellido solo puede contener letras y espacios')
    
    # Validar fecha de nacimiento
    if not datos.get('fechaNacimiento'):
        errores.append('El campo fecha de nacimiento es obligatorio')
    
    # Validar género
    if not datos.get('genero'):
        errores.append('El campo género es obligatorio')
    
    # Validar contacto
    contacto = datos.get('contacto', '')
    if not contacto:
        errores.append('El campo contacto es obligatorio')
    elif not validar_telefono(contacto):
        errores.append('El número de teléfono no es válido. Debe contener entre 8 y 12 dígitos')
    
    # Validar cobertura de salud
    if not datos.get('cobertura_de_salud'):
        errores.append('El campo cobertura de salud es obligatorio')
    
    # Validar trabajo
    trabajo = datos.get('trabajo', '').strip()
    if not trabajo:
        errores.append('El campo trabajo es obligatorio')
    
    # Validar profesión
    profesion = datos.get('profesion', '').strip()
    if not profesion:
        errores.append('El campo profesión es obligatorio')
    
    # Validar fechas de licencia
    if not datos.get('LicenciaInicio'):
        errores.append('El campo fecha de inicio de licencia es obligatorio')
    
    if not datos.get('LicenciaFin'):
        errores.append('El campo fecha de fin de licencia es obligatorio')
    
    # Validar días de licencia
    dias_licencia = datos.get('LicenciaDias', '')
    if not dias_licencia:
        errores.append('El campo días de licencia es obligatorio')
    elif not str(dias_licencia).isdigit() or int(dias_licencia) <= 0:
        errores.append('Los días de licencia deben ser un número entero positivo')
    
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

    try:
        # Verificar si el usuario tiene sesión activa como clínico
        if 'nombre_clinico' not in request.session:
            return redirect('login')

        nombre_clinico = request.session['nombre_clinico']
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')

        context = {}
        
        if request.method == 'GET':
            rut = request.GET.get('rut')
            if rut:
                try:
                    paciente_obj = Paciente.objects.get(rut=rut)
                    context['paciente_existente'] = True
                    context['paciente'] = paciente_obj
                except Paciente.DoesNotExist:
                    pass

        if request.method == 'POST':
            # Parsear duración de sesión y crear registro tiempo
            duracion_sesion_str = request.POST.get('duracion_sesion')
            nuevo_tiempo = parsear_duracion_sesion(duracion_sesion_str)
            if duracion_sesion_str and not nuevo_tiempo:
                messages.error(request, 'Formato de duración de sesión inválido.')

            paciente_ya_existe = request.POST.get('paciente_ya_existe') == 'true'

            if paciente_ya_existe:
                rut = request.POST.get('rut_oculto')
                try:
                    paciente = Paciente.objects.get(rut=rut)
                except Paciente.DoesNotExist:
                    messages.error(request, 'El paciente especificado no existe.')
                    return render(request, 'FormularioInicial.html', context)
            else:
                rut = request.POST.get('rut')
                nombre = request.POST.get('nombre')
                apellido = request.POST.get('apellido')
                fechaNacimiento_raw = request.POST.get('fechaNac')
                genero = request.POST.get('genero')
                contacto = request.POST.get('contact')
                correo = request.POST.get('correo')
                contacto = contacto.replace(' ', '').replace('(', '').replace(')', '').replace('-', '') if contacto else ''
                trabajo = request.POST.get('trabajo')
                profesion = request.POST.get('profesion')
                cobertura_de_salud = request.POST.get('cobertura')
                LicenciaInicio_raw = request.POST.get('fecha_inicio')
                LicenciaFin_raw = request.POST.get('fecha_fin')
                LicenciaDias = request.POST.get('dias_licencia')

                try:
                    resumen = f"POST recibido: rut={rut}, nombre={nombre}, apellido={apellido}"
                    messages.info(request, resumen)
                except Exception:
                    pass

                fechaNacimiento = parsear_fecha_campo(fechaNacimiento_raw, 'fecha de nacimiento', request)
                if fechaNacimiento is None:
                    return render(request, 'FormularioInicial.html', context)

                LicenciaInicio = parsear_fecha_campo(LicenciaInicio_raw, 'fecha de inicio de licencia', request) if LicenciaInicio_raw else None

                datos_para_validar = {
                    'rut': rut,
                    'nombre': nombre,
                    'apellido': apellido,
                    'fechaNacimiento': fechaNacimiento,
                    'genero': genero,
                    'contacto': contacto,
                    'correo': correo,
                    'cobertura_de_salud': cobertura_de_salud,
                    'trabajo': trabajo,
                    'profesion': profesion,
                    'LicenciaInicio': LicenciaInicio_raw,
                    'LicenciaFin': LicenciaFin_raw,
                    'LicenciaDias': LicenciaDias,
                }

                errores = validar_campos_obligatorios(datos_para_validar)
                if errores:
                    for e in errores:
                        messages.error(request, e)
                    return render(request, 'FormularioInicial.html', context)

                defaults = {
                    'nombre': nombre,
                    'apellido': apellido,
                    'fechaNacimiento': fechaNacimiento,
                    'genero': genero,
                    'contacto': contacto,
                    'correo': correo,
                    'cobertura_de_salud': cobertura_de_salud,
                    'trabajo': trabajo,
                    'profesion': profesion,
                    'LicenciaInicio': LicenciaInicio,
                    'LicenciaFin': LicenciaFin_raw if LicenciaFin_raw else None,
                    'LicenciaDias': LicenciaDias,
                }

                try:
                    paciente, created = crear_o_actualizar_paciente(rut, defaults, clinico=clinico)
                    messages.info(request, f"Paciente {'creado' if created else 'actualizado'}: {rut}")
                except Exception as e:
                    messages.error(request, f'Error al crear/actualizar paciente: {e}')
                    return render(request, 'FormularioInicial.html', context)

            # Construir y guardar formulario Clínico con todos los campos
            try:
                construir_formulario_desde_post(request, paciente, clinico, nuevo_tiempo)
                messages.info(request, 'Formulario clínico guardado correctamente.')
            except Exception as e:
                messages.error(request, f'Error al guardar formulario clínico: {e}')
                return render(request, 'FormularioInicial.html', context)
            
            request.session['show_success_message'] = 'Paciente guardado exitosamente.'
            return redirect('panel')

        return render(request, 'FormularioInicial.html', context)

    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado: intenta Nuevamente')
        return render(request, 'FormularioInicial.html')


# ================================
# VISTAS DEL SISTEMA QR
# ================================

def generar_token_formulario(request):
    """Vista para generar un token QR para formularios públicos"""
    try:
        # Verificar sesión de clínico
        if 'nombre_clinico' not in request.session:
            messages.error(request, 'Debes iniciar sesión para generar tokens QR')
            return redirect('login')
        
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')
        
        if request.method == 'POST':
            # Obtener días de expiración del formulario
            dias_expiracion = int(request.POST.get('dias_expiracion', 7))
            
            # Crear nuevo token
            token = TokenFormulario.crear_token(clinico, dias_expiracion)
            
            messages.success(request, f'Token QR generado exitosamente. ID: {token.id}')
            return redirect('descargar_qr', token_id=token.id)
        
        # Mostrar formulario para generar token
        return render(request, 'generar_qr.html', {
            'clinico': clinico,
            'tokens_activos': TokenFormulario.objects.filter(clinico=clinico, activo=True).order_by('-fecha_creacion')[:10]
        })
        
    except Exception as e:
        messages.error(request, f'Error al generar token: {str(e)}')
        return render(request, 'generar_qr.html')


def descargar_qr(request, token_id):
    """Vista para descargar el código QR como imagen"""
    try:
        token = get_object_or_404(TokenFormulario, id=token_id)
        
        # Verificar que el clínico tenga acceso al token
        if 'nombre_clinico' not in request.session:
            messages.error(request, 'Debes iniciar sesión para descargar códigos QR')
            return redirect('login')
        
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')
        
        if token.clinico != clinico and not es_admin:
            messages.error(request, 'No tienes permisos para acceder a este token')
            return redirect('panel')
        
        # Generar URL del formulario público
        formulario_url = request.build_absolute_uri(
            reverse('formulario_publico', kwargs={'token_id': token_id})
        )
        
        # Crear código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(formulario_url)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Crear respuesta HTTP
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="qr_formulario_{token_id}.png"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar código QR: {str(e)}')
        return redirect('generar_qr')


def formulario_publico(request, token_id):
    """Vista pública del formulario accesible mediante QR"""
    try:
        token = get_object_or_404(TokenFormulario, id=token_id)
        
        # Verificar si el token es válido
        if not token.is_valid():
            if token.is_expired():
                return render(request, 'formulario_expirado.html', {
                    'token': token,
                    'mensaje': 'Este formulario ha expirado'
                })
            elif token.usado:
                return render(request, 'formulario_expirado.html', {
                    'token': token,
                    'mensaje': 'Este formulario ya ha sido utilizado'
                })
            else:
                return render(request, 'formulario_expirado.html', {
                    'token': token,
                    'mensaje': 'Este formulario no está disponible'
                })
        
        if request.method == 'POST':
            # Procesar formulario público (formulario inicial completo)
            try:
                # Parsear duración de sesión y crear registro tiempo
                duracion_sesion_str = request.POST.get('duracion_sesion')
                nuevo_tiempo = parsear_duracion_sesion(duracion_sesion_str)
                if duracion_sesion_str and not nuevo_tiempo:
                    messages.error(request, 'Formato de duración de sesión inválido.')

                # Obtener datos básicos del formulario
                rut = request.POST.get('rut')
                nombre = request.POST.get('nombre')
                apellido = request.POST.get('apellido')
                fechaNacimiento_raw = request.POST.get('fechaNac')
                genero = request.POST.get('genero')
                contacto = request.POST.get('contact')
                correo = request.POST.get('correo')
                if contacto:
                    contacto = contacto.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
                trabajo = request.POST.get('trabajo')
                profesion = request.POST.get('profesion')
                cobertura_de_salud = request.POST.get('cobertura')
                LicenciaInicio_raw = request.POST.get('fecha_inicio')
                LicenciaFin_raw = request.POST.get('fecha_fin')
                LicenciaDias = request.POST.get('dias_licencia')

                # Parseo de fechas con mensajes en caso de error
                fechaNacimiento = parsear_fecha_campo(fechaNacimiento_raw, 'fecha de nacimiento', request)
                if fechaNacimiento is None:
                    return render(request, 'FormularioInicial.html', {
                        'token': token,
                        'es_publico': True,
                        'clinico': token.clinico
                    })

                LicenciaInicio = parsear_fecha_campo(LicenciaInicio_raw, 'fecha de inicio de licencia', request)
                if LicenciaInicio is None:
                    return render(request, 'FormularioInicial.html', {
                        'token': token,
                        'es_publico': True,
                        'clinico': token.clinico
                    })

                datos_para_validar = {
                    'rut': rut,
                    'nombre': nombre,
                    'apellido': apellido,
                    'fechaNacimiento': fechaNacimiento,
                    'genero': genero,
                    'contacto': contacto,
                    'correo': correo,
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
                    return render(request, 'FormularioInicial.html', {
                        'token': token,
                        'es_publico': True,
                        'clinico': token.clinico
                    })

                # Crear/actualizar paciente
                defaults = {
                    'nombre': nombre,
                    'apellido': apellido,
                    'fechaNacimiento': fechaNacimiento,
                    'genero': genero,
                    'contacto': contacto,
                    'correo': correo,
                    'cobertura_de_salud': cobertura_de_salud,
                    'trabajo': trabajo,
                    'profesion': profesion,
                    'LicenciaInicio': LicenciaInicio,
                    'LicenciaFin': LicenciaFin_raw,
                    'LicenciaDias': LicenciaDias,
                }

                paciente, created = crear_o_actualizar_paciente(rut, defaults, clinico=token.clinico)
                
                # Marcar token como usado
                token.marcar_como_usado(paciente)

                # Construir y guardar formulario Clínico completo con todos los campos
                try:
                    construir_formulario_desde_post(request, paciente, token.clinico, nuevo_tiempo)
                    messages.info(request, 'Formulario clínico guardado correctamente.')
                except Exception as e:
                    messages.error(request, f'Error al guardar formulario clínico: {e}')
                    return render(request, 'FormularioInicial.html', {
                        'token': token,
                        'es_publico': True,
                        'clinico': token.clinico
                    })
                
                return render(request, 'formulario_exitoso.html', {
                    'mensaje': f'Formulario enviado exitosamente para {nombre} {apellido}',
                    'paciente': paciente,
                    'clinico': token.clinico
                })
                
            except Exception as e:
                messages.error(request, f'Error al procesar el formulario: {str(e)}')
                return render(request, 'FormularioInicial.html', {
                    'token': token,
                    'es_publico': True,
                    'clinico': token.clinico
                })
        
        # Mostrar formulario público (usando el formulario inicial completo)
        return render(request, 'FormularioInicial.html', {
            'token': token,
            'es_publico': True,
            'clinico': token.clinico
        })
        
    except Exception as e:
        return render(request, 'error.html', {
            'mensaje': f'Error al cargar el formulario: {str(e)}'
        })


def desactivar_token(request, token_id):
    """Vista para desactivar un token QR"""
    try:
        # Verificar sesión de clínico
        if 'nombre_clinico' not in request.session:
            messages.error(request, 'Debes iniciar sesión para desactivar tokens')
            return redirect('login')
        
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')
        
        token = get_object_or_404(TokenFormulario, id=token_id)
        
        # Verificar permisos
        if token.clinico != clinico and not es_admin:
            messages.error(request, 'No tienes permisos para desactivar este token')
            return redirect('panel')
        
        # Desactivar token
        token.desactivar()
        messages.success(request, f'Token {token_id} desactivado exitosamente')
        
        return redirect('generar_qr')
        
    except Exception as e:
        messages.error(request, f'Error al desactivar token: {str(e)}')
        return redirect('generar_qr')
    
