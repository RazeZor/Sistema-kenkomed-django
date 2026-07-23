from datetime import datetime, timedelta
import re
from django.shortcuts import render, redirect, get_object_or_404
from Login.models import formularioClinico, Clinico, Paciente
from FormularioInicial.models import TokenFormulario, ConsentimientoDatos
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.urls import reverse
from ProyectoMainAPP.email_service import notificar_nuevo_paciente, notificar_formulario_completado
from clinicas.utils import (
    filtrar_pacientes_por_sesion,
    filtrar_tokens_formulario_por_sesion,
    obtener_clinicos_de_sesion,
    obtener_paciente_por_rut,
    paciente_pertenece_a_sesion,
)
from Login.auditoria import obtener_ip_cliente, registrar_auditoria
from Login.identificacion_context import contexto_identificacion_paciente
from Login.identificacion_utils import (
    TIPO_RUT_CHILE,
    identificacion_ya_existe,
    identificacion_coincide_con_paciente,
    normalizar_identificador,
    resolver_paciente_por_identificacion,
    validar_identificacion,
    validar_rut_chileno,
)
from FormularioInicial.anamnesis_utils import guardar_anamnesis_desde_post, prefill_desde_formulario
import json
import qrcode


def _paciente_puede_anamnesis_qr(request, paciente):
    from ciclos_clinicos.selectors import obtener_ciclo_activo
    from ciclos_clinicos.clinical_data import tiene_anamnesis_ciclo

    clinica_id = request.session.get('clinica_id') or paciente.clinica_id
    ciclo = obtener_ciclo_activo(paciente, clinica_id)
    if ciclo and tiene_anamnesis_ciclo(ciclo):
        return False
    return True


def _pacientes_elegibles_qr(request):
    from ciclos_clinicos.selectors import obtener_ciclo_activo
    from ciclos_clinicos.clinical_data import tiene_anamnesis_ciclo

    clinica_id = request.session.get('clinica_id')
    elegibles = []
    for paciente in filtrar_pacientes_por_sesion(request):
        cid = clinica_id or paciente.clinica_id
        ciclo = obtener_ciclo_activo(paciente, cid)
        if ciclo is None or not tiene_anamnesis_ciclo(ciclo):
            elegibles.append(paciente)
    return elegibles
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

def parsear_fecha_campo(fecha_str, campo_nombre, request):
    """Parsea una fecha en formato YYYY-MM-DD. Si falla, agrega mensaje y retorna None."""
    try:
        return datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except Exception:
        messages.error(request, f'El campo {campo_nombre} debe tener formato YYYY-MM-DD')
        return None

def validar_rut(rut):
    """Compatibilidad: delega en validación RUT chileno."""
    return validar_rut_chileno(rut)


def _datos_identificacion_desde_post(post):
    tipo = post.get('tipo_documento', TIPO_RUT_CHILE)
    pais = post.get('pais_documento', '')
    numero = (post.get('numero_documento') or post.get('rut') or '').strip()
    return tipo, pais, numero


def _identificador_canonico_desde_post(post):
    tipo, pais, numero = _datos_identificacion_desde_post(post)
    return normalizar_identificador(tipo, numero, pais), tipo, pais

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

def validar_campos_obligatorios(datos, permitir_existente=False):
    """Recibe un dict con valores y devuelve una lista de errores por campos vacíos o inválidos."""
    errores = []
    
    # Validar documento de identidad
    tipo_doc = datos.get('tipo_documento', TIPO_RUT_CHILE)
    pais_doc = datos.get('pais_documento', '')
    numero_doc = (datos.get('numero_documento') or datos.get('rut', '')).strip()
    if not numero_doc:
        errores.append('El número de documento es obligatorio')
    else:
        ok, msg = validar_identificacion(tipo_doc, numero_doc, pais_doc)
        if not ok:
            errores.append(msg)
        elif not permitir_existente and identificacion_ya_existe(tipo_doc, numero_doc, pais_doc):
            errores.append('Este documento ya está registrado en el sistema')
    
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
    
    # Validar correo electrónico
    correo = datos.get('correo', '').strip()
    if not correo:
        errores.append('El correo electrónico es obligatorio para enviar notificaciones al paciente')
    elif '@' not in correo or '.' not in correo.split('@')[-1]:
        errores.append('El correo electrónico ingresado no tiene un formato válido')
    
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

def crear_o_actualizar_paciente(rut, defaults, clinico=None, tipo_documento=TIPO_RUT_CHILE, pais_documento=''):
    """Crea o actualiza el paciente. `rut` es el identificador canónico."""
    defaults = dict(defaults)
    defaults['tipo_documento'] = tipo_documento
    defaults['pais_documento'] = pais_documento or ''
    paciente, created = Paciente.objects.update_or_create(rut=rut, defaults=defaults)
    if clinico:
        try:
            paciente.clinico = clinico
            paciente.clinico_creador = clinico
            # Buscar clínica activa del clínico
            from clinicas.models import MembresiaClinica
            membresia = MembresiaClinica.objects.filter(clinico=clinico, activo=True).first()
            if membresia:
                paciente.clinica = membresia.clinica
            paciente.save()
        except Exception as e:
            # Si no existe el campo clinico o falla, no interrumpimos el flujo
            print(f"Error al asociar clinica/clinico al paciente: {e}")
    elif 'clinica_id' in defaults:
        # Fallback si se especifica la clínica directamente
        try:
            paciente.clinica_id = defaults['clinica_id']
            paciente.save()
        except Exception:
            pass
    return paciente, created


def construir_formulario_desde_post(request, paciente, clinico):
    """Construye y guarda el objeto formularioClinico a partir de request.POST."""
    form, _ = guardar_anamnesis_desde_post(request, paciente, clinico)
    return form


def _contexto_anamnesis_paciente(request, paciente):
    """Contexto extra cuando el clínico abre el formulario con un paciente."""
    from ciclos_clinicos.services import obtener_ciclo_desde_request, CicloClinicoError, asegurar_ciclo_editable
    from ciclos_clinicos.context_helpers import contexto_ciclo_para_template
    from ciclos_clinicos.clinical_data import formulario_del_ciclo

    ctx = {
        'paciente_existente': True,
        'paciente': paciente,
        'modo_edicion': False,
    }
    ctx.update(contexto_identificacion_paciente(paciente))
    clinico, _ = obtener_clinico_desde_sesion(request)
    ciclo = obtener_ciclo_desde_request(request, paciente, crear_si_ausente=False, clinico=clinico)
    ctx.update(contexto_ciclo_para_template(ciclo, paciente))
    form = formulario_del_ciclo(ciclo) if ciclo else None
    if form:
        ctx['modo_edicion'] = True
        ctx['formulario_existente'] = form
        ctx['anamnesis_prefill'] = prefill_desde_formulario(form)
    return ctx

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

        context = contexto_identificacion_paciente()
        
        if request.method == 'GET':
            rut = request.GET.get('rut')
            if rut:
                paciente_obj = obtener_paciente_por_rut(request, rut)
                if paciente_obj:
                    context.update(_contexto_anamnesis_paciente(request, paciente_obj))
                    registrar_auditoria(
                        request, 'consulta_formulario_inicial', paciente_obj,
                        detalle=(
                            f'Accedió a editar anamnesis — {paciente_obj.rut}'
                            if context.get('modo_edicion')
                            else f'Accedió a anamnesis DSS — {paciente_obj.rut}'
                        ),
                    )

        if request.method == 'POST':
            paciente_ya_existe = request.POST.get('paciente_ya_existe') == 'true'

            if paciente_ya_existe:
                rut = request.POST.get('rut_oculto')
                paciente = obtener_paciente_por_rut(request, rut)
                if not paciente:
                    messages.error(request, 'El paciente especificado no existe o no pertenece a tu clínica.')
                    return render(request, 'FormularioInicial.html', context)
            else:
                rut = request.POST.get('rut')
                nombre = request.POST.get('nombre')
                apellido = request.POST.get('apellido')
                tipo_doc, pais_doc, numero_doc = _datos_identificacion_desde_post(request.POST)
                identificador, tipo_doc, pais_doc = _identificador_canonico_desde_post(request.POST)
                fechaNacimiento_raw = request.POST.get('fechaNac')
                genero = request.POST.get('genero')
                contacto = request.POST.get('contact')
                correo = request.POST.get('correo')
                contacto = contacto.replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '') if contacto else ''
                if contacto and len(contacto) <= 8 and not contacto.startswith('56'):
                    contacto = '569' + contacto
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
                    'tipo_documento': tipo_doc,
                    'pais_documento': pais_doc,
                    'numero_documento': numero_doc,
                    'rut': numero_doc,
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

                errores = validar_campos_obligatorios(datos_para_validar, permitir_existente=True)
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
                    paciente, created = crear_o_actualizar_paciente(
                        identificador, defaults, clinico=clinico,
                        tipo_documento=tipo_doc, pais_documento=pais_doc,
                    )
                    messages.info(request, f"Paciente {'creado' if created else 'actualizado'}: {paciente.identificacion_display()}")
                    # Enviar correo de bienvenida al nuevo paciente y aviso al clínico
                    if created and clinico:
                        notificar_nuevo_paciente(paciente, clinico)
                    elif not created and clinico and correo and not getattr(paciente, 'correo', None):
                        # Si el paciente ya existía pero ahora se le agrega correo, notificar igual
                        paciente.correo = correo
                        paciente.save()
                        notificar_nuevo_paciente(paciente, clinico)
                except Exception as e:
                    messages.error(request, f'Error al crear/actualizar paciente: {e}')
                    return render(request, 'FormularioInicial.html', context)

            # Construir y guardar formulario Clínico con todos los campos
            try:
                es_edicion_previa = request.POST.get('editar_anamnesis') == 'true'
                form, fue_edicion = guardar_anamnesis_desde_post(request, paciente, clinico)
                registrar_auditoria(
                    request, 'edicion_anamnesis', paciente,
                    detalle=(
                        f'Anamnesis actualizada por clínico — {paciente.rut}'
                        if fue_edicion or es_edicion_previa
                        else f'Anamnesis DSS guardada desde panel — {paciente.rut}'
                    ),
                )
                messages.success(
                    request,
                    'Anamnesis actualizada correctamente.' if fue_edicion else 'Formulario clínico guardado correctamente.',
                )
            except Exception as e:
                messages.error(request, f'Error al guardar formulario clínico: {e}')
                if paciente:
                    context.update(_contexto_anamnesis_paciente(request, paciente))
                return render(request, 'FormularioInicial.html', context)

            if request.POST.get('editar_anamnesis') == 'true' or request.POST.get('paciente_ya_existe') == 'true':
                return redirect(f"{reverse('historialClinico')}?rut={paciente.rut}")

            request.session['show_success_message'] = 'Paciente guardado exitosamente.'
            return redirect('panel')

        return render(request, 'FormularioInicial.html', context)

    except Exception as e:
        messages.error(request, f'Ocurrió un error inesperado: intenta Nuevamente')
        return render(request, 'FormularioInicial.html')


# ================================
# SISTEMA DE FORMULARIOS REMOTOS
# ================================

def generar_token_formulario(request):
    """Gestor de formularios remotos. Genera tokens vinculados a pacientes pre-registrados."""
    try:
        if 'nombre_clinico' not in request.session:
            messages.error(request, 'Debes iniciar sesión')
            return redirect('login')
        
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')
        
        if request.method == 'POST':
            rut_paciente = request.POST.get('rut_paciente', '').strip()
            dias_expiracion = int(request.POST.get('dias_expiracion', 7))
            
            if not rut_paciente:
                messages.error(request, 'Debes seleccionar un paciente')
                return redirect('generar_qr')
            
            try:
                paciente = Paciente.objects.get(rut=rut_paciente)
            except Paciente.DoesNotExist:
                messages.error(request, 'Paciente no encontrado en el sistema')
                return redirect('generar_qr')

            if not paciente_pertenece_a_sesion(request, paciente):
                messages.error(request, 'No tienes permisos para generar formulario para este paciente')
                return redirect('generar_qr')
            
            if not _paciente_puede_anamnesis_qr(request, paciente):
                messages.warning(request, f'{paciente.nombre} {paciente.apellido} ya completó la anamnesis del ciclo activo.')
                return redirect('generar_qr')
            
            # Desactivar tokens anteriores del mismo paciente
            TokenFormulario.objects.filter(paciente=paciente, activo=True).update(activo=False)
            
            # Crear nuevo token
            token = TokenFormulario.crear_token(clinico, paciente, dias_expiracion)

            registrar_auditoria(
                request, 'qr_generar', paciente,
                detalle=f'Generó formulario remoto QR — expira en {dias_expiracion} días',
            )
            
            messages.success(request, f'Formulario remoto generado para {paciente.nombre} {paciente.apellido}')
            return redirect('descargar_qr', token_id=token.id)
        
        # GET: Listar pacientes sin anamnesis y tokens activos
        pacientes_sin_anamnesis = _pacientes_elegibles_qr(request)

        tokens_activos = filtrar_tokens_formulario_por_sesion(request).order_by('-fecha_creacion')[:20]
        
        return render(request, 'generar_qr.html', {
            'clinico': clinico,
            'pacientes_sin_anamnesis': pacientes_sin_anamnesis,
            'tokens_activos': tokens_activos,
        })
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return render(request, 'generar_qr.html')


def descargar_qr(request, token_id):
    """Muestra QR + link copiable para compartir con el paciente."""
    try:
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')
        
        token = get_object_or_404(TokenFormulario, id=token_id)
        
        if not paciente_pertenece_a_sesion(request, token.paciente):
            messages.error(request, 'No tienes permisos')
            return redirect('panel')
        
        # Generar URL del formulario
        formulario_url = request.build_absolute_uri(
            reverse('formulario_publico', kwargs={'token_id': token_id})
        )
        
        # Generar QR como base64 para mostrar en pantalla
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(formulario_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Formatear número de teléfono con código país Chile (+56)
        telefono = token.paciente.contacto or ''
        telefono = telefono.replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '')
        # Si empieza con 56, ya tiene código país
        if not telefono.startswith('56'):
            # Si empieza con 9 (celular chileno), agregar 56
            if telefono.startswith('9') and len(telefono) == 9:
                telefono = '56' + telefono
            else:
                telefono = '56' + telefono
        
        # Mensaje WhatsApp pre-armado
        from urllib.parse import quote
        whatsapp_msg = f"Hola {token.paciente.nombre}, te envío el formulario médico de KenkoMed para que completes tu historial antes de tu cita. Ingresa aquí: {formulario_url}"
        whatsapp_url = f"https://wa.me/{telefono}?text={quote(whatsapp_msg)}"
        
        return render(request, 'mostrar_qr_link.html', {
            'token': token,
            'formulario_url': formulario_url,
            'qr_base64': qr_base64,
            'whatsapp_url': whatsapp_url,
            'clinico': clinico,
        })
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('generar_qr')


def formulario_publico(request, token_id):
    """Vista pública: Verificación RUT + formulario de anamnesis (solo DSS)."""
    try:
        token = get_object_or_404(TokenFormulario, id=token_id)
        
        if not token.is_valid():
            if token.usado:
                msg = 'Este formulario ya fue completado'
            elif token.is_expired():
                msg = 'Este formulario ha expirado'
            else:
                msg = 'Este formulario no está disponible'
            return render(request, 'formulario_expirado.html', {'token': token, 'mensaje': msg})
        
        paciente = token.paciente
        
        # PASO 1: Verificación de identidad
        rut_verificado = request.session.get(f'rut_verificado_{token_id}', False)
        es_rut = getattr(paciente, 'tipo_documento', TIPO_RUT_CHILE) == TIPO_RUT_CHILE
        ctx_verificacion = {
            'token': token,
            'nombre_paciente': paciente.nombre,
            'es_rut_chile': es_rut,
            'identificacion_hint': paciente.identificacion_display(),
        }
        
        if not rut_verificado:
            if request.method == 'POST' and 'rut_verificacion' in request.POST:
                rut_input = request.POST.get('rut_verificacion', '').strip()
                
                if identificacion_coincide_con_paciente(paciente, rut_input):
                    request.session[f'rut_verificado_{token_id}'] = True
                    rut_verificado = True
                else:
                    messages.error(
                        request,
                        'El documento ingresado no coincide con el registro. Verifica e intenta nuevamente.',
                    )
                    return render(request, 'formulario_verificar_rut.html', ctx_verificacion)
            
            if not rut_verificado:
                return render(request, 'formulario_verificar_rut.html', ctx_verificacion)
        
        # PASO 2: Formulario de anamnesis
        if request.method == 'POST' and 'rut_verificacion' not in request.POST:
            if request.POST.get('consentimiento_datos') != 'on':
                messages.error(
                    request,
                    'Debe leer y aceptar el aviso de tratamiento de datos personales para enviar el formulario.',
                )
                return render(request, 'FormularioInicial.html', {
                    'token': token,
                    'es_publico': True,
                    'es_solo_anamnesis': True,
                    'paciente_existente': True,
                    'paciente': paciente,
                    'clinico': token.clinico,
                    'clinica': paciente.clinica,
                })

            try:
                # Guardar formulario clínico con datos del paciente pre-existente
                construir_formulario_desde_post(request, paciente, token.clinico)

                ConsentimientoDatos.objects.create(
                    paciente=paciente,
                    clinica=paciente.clinica,
                    origen='formulario_qr',
                    ip_address=obtener_ip_cliente(request),
                    token=token,
                )

                registrar_auditoria(
                    request, 'formulario_qr_enviado', paciente,
                    detalle=f'Paciente completó anamnesis vía QR — {paciente.rut}',
                )
                
                # Marcar token como usado
                token.marcar_como_usado()
                
                # Notificar al clínico que el paciente completó el formulario
                notificar_formulario_completado(paciente, token.clinico)
                
                # Limpiar sesión de verificación
                if f'rut_verificado_{token_id}' in request.session:
                    del request.session[f'rut_verificado_{token_id}']
                
                return render(request, 'formulario_exitoso.html', {
                    'mensaje': f'¡Formulario enviado exitosamente!',
                    'paciente': paciente,
                    'clinico': token.clinico
                })
                
            except Exception as e:
                messages.error(request, f'Error al guardar: {str(e)}')
        
        # Mostrar formulario con datos del paciente pre-llenados (readonly)
        return render(request, 'FormularioInicial.html', {
            'token': token,
            'es_publico': True,
            'es_solo_anamnesis': True,
            'paciente_existente': True,
            'paciente': paciente,
            'clinico': token.clinico,
            'clinica': paciente.clinica,
        })
        
    except Exception as e:
        return render(request, 'formulario_expirado.html', {
            'mensaje': f'Error al cargar el formulario'
        })


def desactivar_token(request, token_id):
    """Desactiva un token de formulario remoto."""
    try:
        if 'nombre_clinico' not in request.session:
            return redirect('login')
        
        clinico, es_admin = obtener_clinico_desde_sesion(request)
        if not clinico and not es_admin:
            return redirect('login')
        
        token = get_object_or_404(TokenFormulario, id=token_id)
        
        if not paciente_pertenece_a_sesion(request, token.paciente):
            messages.error(request, 'No tienes permisos')
            return redirect('panel')
        
        token.desactivar()
        registrar_auditoria(
            request, 'qr_desactivar', token.paciente,
            detalle=f'Desactivó formulario remoto — {token.paciente.rut}',
        )
        messages.success(request, f'Formulario de {token.paciente.nombre} {token.paciente.apellido} desactivado')
        
        return redirect('generar_qr')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('generar_qr')


def aviso_privacidad_paciente(request):
    """Aviso público de tratamiento de datos (pacientes — formulario QR)."""
    return render(request, 'privacidad_paciente.html')


def generar_token_desde_historial(request):
    """Genera token rápido desde el historial clínico del paciente (AJAX-friendly)."""
    if request.method != 'POST':
        return redirect('panel')
    
    if 'nombre_clinico' not in request.session:
        return redirect('login')
    
    clinico, es_admin = obtener_clinico_desde_sesion(request)
    if not clinico and not es_admin:
        return redirect('login')
    
    rut = request.POST.get('rut', '').strip()
    try:
        paciente = Paciente.objects.get(rut=rut)
    except Paciente.DoesNotExist:
        messages.error(request, 'Paciente no encontrado')
        return redirect('historialClinico')
    
    if not _paciente_puede_anamnesis_qr(request, paciente):
        messages.warning(request, f'{paciente.nombre} ya completó la anamnesis del ciclo activo.')
        return redirect(f'/panel/historialClinico/?rut={rut}')
    
    # Desactivar tokens anteriores
    TokenFormulario.objects.filter(paciente=paciente, activo=True).update(activo=False)
    
    token = TokenFormulario.crear_token(clinico, paciente, dias_expiracion=7)

    registrar_auditoria(
        request, 'qr_generar', paciente,
        detalle='Generó formulario remoto QR desde historial clínico',
    )
    
    return redirect('descargar_qr', token_id=token.id)

    
