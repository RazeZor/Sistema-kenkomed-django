from django.shortcuts import redirect, render
from Login.models import Clinico, formularioClinico
from django.contrib import messages

def obtener_perfil_clinico(nombre_clinico):
    try:
        perfil = Clinico.objects.filter(nombre__iexact=nombre_clinico.split()[0],
                                         apellido__iexact=" ".join(nombre_clinico.split()[1:])).first()
        return perfil
    except Exception as e:
        print(f"Error al obtener perfil clínico: {e}")
        return None

def obtener_pacientes_atendidos(perfil):
    try:
        if perfil:
            pacientes_atendidos = formularioClinico.objects.filter(clinico=perfil).count()
            return pacientes_atendidos
        return 0
    except Exception as e:
        print(f"Error al obtener pacientes atendidos: {e}")
        return 0

def RenderizarPerfil(request):
    try:
        # Verificar sesión
        if 'nombre_clinico' not in request.session:
            return render(request, 'login.html')
        
        nombre_clinico = request.session['nombre_clinico']
        perfil = obtener_perfil_clinico(nombre_clinico)
        
        if not perfil:
            return render(request, 'perfil.html', {'error': 'Perfil no encontrado'})
        
        # Manejar POST - Actualizar perfil
        if request.method == 'POST':
            try:
                # Actualizar solo los campos permitidos
                perfil.correo = request.POST.get('correo', perfil.correo)
                perfil.telefono = request.POST.get('telefono', perfil.telefono)
                perfil.centro_trabajo = request.POST.get('centro_trabajo', perfil.centro_trabajo)
                perfil.ciudad = request.POST.get('ciudad', perfil.ciudad)
                perfil.especialidad = request.POST.get('especialidad', perfil.especialidad)
                perfil.numero_registro = request.POST.get('numero_registro', perfil.numero_registro)
                perfil.descripcion = request.POST.get('descripcion', perfil.descripcion)
                
                # Manejar experiencia (puede venir vacío)
                experiencia = request.POST.get('experiencia')
                if experiencia and experiencia.strip():
                    perfil.experiencia = int(experiencia)
                
                perfil.save()
                messages.success(request, '¡Perfil actualizado exitosamente!')
                
            except ValueError:
                messages.error(request, 'Años de experiencia debe ser un número válido.')
            except Exception as e:
                messages.error(request, f'Error al actualizar el perfil: {str(e)}')
                print(f"Error al actualizar perfil: {e}")
        
        # Obtener pacientes atendidos (tanto para GET como POST)
        pacientes_atendidos = obtener_pacientes_atendidos(perfil)
        
        # Renderizar la página (tanto para GET como después de POST)
        return render(request, 'perfil.html', {
            'nombre_clinico': nombre_clinico,
            'pacientesAtendidos': pacientes_atendidos,
            'perfil': perfil,
            'es_admin': request.session.get('es_admin', False),
        })
        
    except Exception as e:
        print(f"Error en RenderizarPerfil: {e}")
        messages.error(request, f'Hubo un problema al cargar el perfil. Intente nuevamente más tarde.{e}')
        return redirect('login')