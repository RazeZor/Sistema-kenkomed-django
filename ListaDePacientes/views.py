from django.shortcuts import get_object_or_404, redirect, render
from Login.models import Paciente
from django.core.paginator import Paginator
from django.contrib import messages

def MostrarPacientes(request):
    if 'nombre_clinico' in request.session:
        nombre_clinico = request.session['nombre_clinico']
        es_admin = request.session.get('es_admin', False)

        pacientes = Paciente.objects.all() #select * from paciente
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