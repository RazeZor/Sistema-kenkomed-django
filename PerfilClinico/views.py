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
            rut = perfil.rut  # Obtener el RUT del clínico
            pacientes_atendidos = formularioClinico.objects.filter(clinico=perfil).count()
            return pacientes_atendidos
        return 0
    except Exception as e:
        print(f"Error al obtener pacientes atendidos: {e}")
        return 0

def RenderizarPerfil(request):
    try:
        if 'nombre_clinico' in request.session:
            nombre_clinico = request.session['nombre_clinico']
            
            # Obtener el perfil del clínico
            perfil = obtener_perfil_clinico(nombre_clinico)

            if perfil:
                # Obtener pacientes atendidos
                pacientes_atendidos = obtener_pacientes_atendidos(perfil)

                return render(request, 'perfil.html', {
                    'nombre_clinico': nombre_clinico,
                    'pacientesAtendidos': pacientes_atendidos,
                    'perfil': perfil,
                    'es_admin': request.session.get('es_admin', False),
                })
            else:
                return render(request, 'perfil.html', {'error': 'Perfil no encontrado'})
        else:
            return render(request, 'login.html')  # Si no hay sesión, redirigir a login
    except Exception as e:
        print(f"Error en RenderizarPerfil: {e}")
        messages.error(request, 'Hubo un problema al cargar el perfil. Intente nuevamente más tarde.')
        return redirect('login')  # Redirigir al login en caso de error
