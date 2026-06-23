from django.shortcuts import redirect, render
from django.contrib import messages
from Login.models import Clinico, Paciente
from clinicas.models import MembresiaClinica
from clinicas.utils import filtrar_pacientes_por_sesion

def RenderizarPerfil(request):
    try:
        # Verificar sesión
        if 'rut_clinico' not in request.session:
            return redirect('login')
        
        rut_clinico = request.session['rut_clinico']
        perfil = Clinico.objects.filter(rut=rut_clinico).first()
        
        if not perfil:
            messages.error(request, 'Perfil no encontrado.')
            return redirect('login')
        
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
                else:
                    perfil.experiencia = None
                
                perfil.save()
                messages.success(request, '¡Perfil actualizado exitosamente!')
                
            except ValueError:
                messages.error(request, 'Años de experiencia debe ser un número válido.')
            except Exception as e:
                messages.error(request, f'Error al actualizar el perfil: {str(e)}')
        
        # Obtener pacientes atendidos (en la clínica de este clínico)
        clinica_id = request.session.get('clinica_id')
        if clinica_id:
            pacientes_atendidos = Paciente.objects.filter(clinica_id=clinica_id).count()
        else:
            pacientes_atendidos = filtrar_pacientes_por_sesion(request).count()
        
        # Obtener clínica actual y membresía para mostrar en la interfaz
        membresia = MembresiaClinica.objects.filter(clinico=perfil, activo=True).first()
        clinica = membresia.clinica if membresia else None
        
        # Renderizar la página
        return render(request, 'perfil.html', {
            'nombre_clinico': f"{perfil.nombre} {perfil.apellido}",
            'pacientesAtendidos': pacientes_atendidos,
            'perfil': perfil,
            'clinica': clinica,
            'membresia': membresia,
            'es_admin': request.session.get('es_admin', False),
        })
        
    except Exception as e:
        messages.error(request, f'Hubo un problema al cargar el perfil: {str(e)}')
        return redirect('login')
