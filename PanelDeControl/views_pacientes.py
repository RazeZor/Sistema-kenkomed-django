from django.shortcuts import get_object_or_404, redirect, render
from Login.auditoria import registrar_auditoria
from Login.models import Paciente, Clinico
from django.core.paginator import Paginator
from django.contrib import messages
from FormularioInicial.views import (
    validar_campos_obligatorios,
    crear_o_actualizar_paciente,
    parsear_fecha_campo,
    _datos_identificacion_desde_post,
    _identificador_canonico_desde_post,
)
from Login.identificacion_context import contexto_identificacion_paciente
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from clinicas.utils import filtrar_pacientes_por_sesion, obtener_paciente_por_rut, paciente_pertenece_a_sesion, requiere_centro_o_admin_sistema

@requiere_clinico
def MostrarPacientes(request):
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)
        es_admin_clinica = request.session.get('es_admin_clinica', False)

        pacientes = filtrar_pacientes_por_sesion(request)

        paginacion = Paginator(pacientes, 10)  # 10 pacientes por página
        pagina = request.GET.get('page')
        paginacion_Pacientes = paginacion.get_page(pagina)

        registrar_auditoria(
            request, 'consulta_lista_pacientes', paciente=None,
            detalle='Consultó listado de pacientes del centro',
        )

        return render(request, 'ListaPacientes.html', {
            'nombre_clinico': nombre_clinico,
            'es_admin': es_admin,
            'es_admin_clinica': es_admin_clinica,
            'paginacion_Pacientes': paginacion_Pacientes,
        })
    else:
        return redirect('login')


@requiere_clinico
def EliminarPaciente(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')  # Obtener el RUT del paciente a eliminar
        try:
            paciente = get_object_or_404(Paciente, rut=rut)
            if not paciente_pertenece_a_sesion(request, paciente):
                messages.error(request, 'No tienes permisos para eliminar este paciente.')
                return redirect('pacientes')

            registrar_auditoria(
                request, 'eliminacion_paciente', paciente,
                detalle=f'Eliminó ficha de {paciente.nombre} {paciente.apellido} ({paciente.rut})',
            )
            paciente.delete()
            messages.success(request, 'Paciente eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el paciente: {e}')
    return redirect('pacientes')  


@requiere_clinico
def AgregarPacienteBasico(request):
    if 'nombre_clinico' not in request.session:
        return redirect('login')

    if not requiere_centro_o_admin_sistema(request):
        messages.error(request, 'Debes tener un centro asociado para registrar pacientes.')
        return redirect('panel')

    nombre_clinico = request.session['nombre_clinico']
    rut_clinico = request.session.get('rut_clinico')
    es_admin = request.session.get('es_admin', False)

    try:
        clinico = Clinico.objects.get(rut=rut_clinico)
    except Clinico.DoesNotExist:
        if not es_admin:
            messages.error(request, 'Clínico no encontrado.')
            return redirect('login')
        clinico = None

    ctx_base = {'nombre_clinico': nombre_clinico, **contexto_identificacion_paciente()}

    if request.method == 'POST':
        tipo_doc, pais_doc, numero_doc = _datos_identificacion_desde_post(request.POST)
        identificador, tipo_doc, pais_doc = _identificador_canonico_desde_post(request.POST)
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fechaNacimiento_raw = request.POST.get('fechaNacimiento')
        genero = request.POST.get('genero')
        contacto = request.POST.get('contacto', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '')
        # Agregar prefijo chileno si solo son los 8 dígitos del celular
        if contacto and len(contacto) <= 8 and not contacto.startswith('56'):
            contacto = '569' + contacto
        correo = request.POST.get('correo')
        cobertura_de_salud = request.POST.get('cobertura_de_salud')
        trabajo = request.POST.get('trabajo', '')
        profesion = request.POST.get('profesion', '')
        LicenciaInicio_raw = request.POST.get('LicenciaInicio', '')
        LicenciaFin_raw = request.POST.get('LicenciaFin', '')
        LicenciaDias = request.POST.get('LicenciaDias', '')

        # Validaciones de fechas usando las funciones importadas
        fechaNacimiento = parsear_fecha_campo(fechaNacimiento_raw, 'fecha de nacimiento', request)
        if fechaNacimiento is None:
            return render(request, 'AgregarPaciente.html', ctx_base)
            
        LicenciaInicio = parsear_fecha_campo(LicenciaInicio_raw, 'fecha de inicio de licencia', request) if LicenciaInicio_raw else None
        LicenciaFin = parsear_fecha_campo(LicenciaFin_raw, 'fecha de fin de licencia', request) if LicenciaFin_raw else None
        if (LicenciaInicio_raw and LicenciaInicio is None) or (LicenciaFin_raw and LicenciaFin is None):
            return render(request, 'AgregarPaciente.html', ctx_base)

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
        
        errores = validar_campos_obligatorios(datos_para_validar)
        
        # Alta manual: trabajo, profesión, licencia y correo son opcionales
        errores_filtrados = [
            e for e in errores
            if not any(k in e.lower() for k in ('licencia', 'trabajo', 'profesión', 'profesion', 'correo'))
        ]
        
        if errores_filtrados:
            for e in errores_filtrados:
                messages.error(request, e)
            return render(request, 'AgregarPaciente.html', ctx_base)

        clinica_id = request.session.get('clinica_id')

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
            'LicenciaFin': LicenciaFin,
            'LicenciaDias': LicenciaDias or '',
            'clinica_id': clinica_id,
        }

        try:
            paciente, created = crear_o_actualizar_paciente(
                identificador, defaults, clinico=clinico,
                tipo_documento=tipo_doc, pais_documento=pais_doc,
            )
            if created:
                registrar_auditoria(
                    request, 'alta_paciente', paciente,
                    detalle=f'Alta manual — {paciente.nombre} {paciente.apellido} ({paciente.identificacion_display()})',
                )
            messages.success(request, f"Paciente {nombre} {apellido} registrado exitosamente.")

            from ciclos_clinicos.services import iniciar_nuevo_ciclo
            try:
                if paciente.clinica_id and clinico:
                    iniciar_nuevo_ciclo(paciente, paciente.clinica, clinico, request=request)
            except Exception:
                pass
            
            request.session['temp_rut_historial'] = paciente.rut
            return redirect('historialClinico')

        except Exception as e:
            messages.error(request, f'Error al registrar paciente: {e}')
            return render(request, 'AgregarPaciente.html', ctx_base)

    return render(request, 'AgregarPaciente.html', ctx_base)


@requiere_clinico
def EditarPaciente(request):
    """Permite al clínico editar los datos básicos de un paciente."""
    if 'nombre_clinico' not in request.session:
        return redirect('login')

    rut = request.GET.get('rut') or request.POST.get('rut')
    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        messages.error(request, 'No tienes permisos para acceder a este paciente.')
        return redirect('pacientes')

    if request.method == 'POST':
        paciente.nombre = request.POST.get('nombre', paciente.nombre).strip()
        paciente.apellido = request.POST.get('apellido', paciente.apellido).strip()
        paciente.correo = request.POST.get('correo', paciente.correo).strip()
        paciente.profesion = request.POST.get('profesion', paciente.profesion).strip()
        paciente.cobertura_de_salud = request.POST.get('cobertura_de_salud', paciente.cobertura_de_salud)

        # Teléfono con prefijo chileno
        contacto_raw = request.POST.get('contacto', '').replace(' ', '').replace('+', '').replace('-', '')
        if contacto_raw:
            if len(contacto_raw) <= 9 and not contacto_raw.startswith('56'):
                contacto_raw = '56' + contacto_raw
            paciente.contacto = contacto_raw

        # Género
        genero = request.POST.get('genero')
        if genero:
            paciente.genero = genero

        # Fecha nacimiento
        fecha_raw = request.POST.get('fechaNacimiento')
        if fecha_raw:
            fecha = parsear_fecha_campo(fecha_raw, 'fecha de nacimiento', request)
            if fecha:
                paciente.fechaNacimiento = fecha

        paciente.save()
        registrar_auditoria(
            request, 'edicion_paciente', paciente,
            detalle=f'Modificó datos demográficos — {paciente.rut}',
        )
        messages.success(request, f'Datos de {paciente.nombre} {paciente.apellido} actualizados correctamente.')
        return redirect(f'/panel/historialClinico/?rut={rut}')

    return render(request, 'EditarPaciente.html', {
        'paciente': paciente,
        'nombre_clinico': request.session.get('nombre_clinico'),
        **contexto_identificacion_paciente(paciente),
    })
