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