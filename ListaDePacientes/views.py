from django.shortcuts import get_object_or_404, redirect, render
from Login.models import Paciente, Clinico
from django.core.paginator import Paginator
from django.contrib import messages

def MostrarPacientes(request):
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)

        # Si es administrador ver todos, sino mostrar solo los pacientes asignados al clínico en sesión
        if es_admin:
            pacientes = Paciente.objects.all()
        else:
            rut_clinico = request.session.get('rut_clinico')
            if not rut_clinico:
                messages.error(request, 'Debe iniciar sesión como clínico para ver sus pacientes.')
                return redirect('login')
            try:
                clinico = Clinico.objects.get(rut=rut_clinico)
            except Clinico.DoesNotExist:
                messages.error(request, 'El clínico de la sesión no existe. Inicie sesión nuevamente.')
                return redirect('login')

            pacientes = Paciente.objects.filter(clinico=clinico)
        paginacion = Paginator(pacientes, 10)  # 10 pacientes por página
        pagina = request.GET.get('page')
        paginacion_Pacientes = paginacion.get_page(pagina)

        return render(request, 'ListaPacientes.html', {
            'nombre_clinico': nombre_clinico,
            'es_admin': es_admin,
            'paginacion_Pacientes': paginacion_Pacientes,  # Enviar solo la paginación
        })
    else:
        return redirect('login')



def EliminarPaciente(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')  # Obtener el RUT del paciente a eliminar
        try:
            paciente = get_object_or_404(Paciente, rut=rut)
            paciente.delete()
            messages.success(request, 'Paciente eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar el paciente: {e}')
    return redirect('pacientes')  

from FormularioInicial.views import validar_campos_obligatorios, crear_o_actualizar_paciente, parsear_fecha_campo

def AgregarPacienteBasico(request):
    if 'nombre_clinico' not in request.session:
        return redirect('login')

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

    if request.method == 'POST':
        rut = request.POST.get('rut')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        fechaNacimiento_raw = request.POST.get('fechaNacimiento')
        genero = request.POST.get('genero')
        contacto = request.POST.get('contacto', '').replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
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
            return render(request, 'AgregarPaciente.html', {'nombre_clinico': nombre_clinico})
            
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
            'LicenciaInicio': LicenciaInicio_raw, # temporalmente pasa raw para validaciones
            'LicenciaFin': LicenciaFin_raw,
            'LicenciaDias': LicenciaDias,
        }

        # Podemos obviar los de licencia si no son estrictamente obligatorios en el basico
        # Pero si validar_campos_obligatorios exige licencia, mandaremos 'Sin información' o datos base
        # Haremos una validación manual basica o bypass
        
        errores = validar_campos_obligatorios(datos_para_validar)
        
        # Filtramos errores de licencia si decidieron dejarlo pelado
        errores_filtrados = [e for e in errores if 'licencia' not in e.lower() and 'trabajo' not in e.lower() and 'profesión' not in e.lower()]
        
        if errores_filtrados:
            for e in errores_filtrados:
                messages.error(request, e)
            return render(request, 'AgregarPaciente.html', {'nombre_clinico': nombre_clinico})

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
            messages.success(request, f"Paciente {nombre} {apellido} registrado exitosamente.")
            
            # Simulamos el redireccionamiento mandando rut al historial (esto se usa a través de POST en HistorialClinico)
            # Como historialClinico es POST o requiere form, lo más limpio es enviarlo con un form temporal o sesión
            # Para esto podemos redirigir a 'historialClinico' pero usando session temporal
            request.session['temp_rut_historial'] = rut
            
            # Vamos al historial
            return redirect('historialClinico')

        except Exception as e:
            messages.error(request, f'Error al registrar paciente: {e}')
            return render(request, 'AgregarPaciente.html', {'nombre_clinico': nombre_clinico})

    return render(request, 'AgregarPaciente.html', {
        'nombre_clinico': nombre_clinico
    })