from pyexpat.errors import messages
from django.shortcuts import get_object_or_404, redirect, render
from Login.models import Clinico
from django.contrib import messages
import re
def AgregarClinico(request):
    if 'nombre_clinico' in request.session:
        if request.method == 'POST':
            rut = request.POST.get('rut', '').strip()
            nombre = request.POST.get('nombre', '').strip()
            apellido = request.POST.get('apellido', '').strip()
            profesion = request.POST.get('profesion', '').strip()
            contraseña = request.POST.get('contraseña', '').strip()

            # Validación de campos vacíos
            if not all([rut, nombre, apellido, profesion, contraseña]):
                messages.error(request, 'Hay campos sin completar.')
                return render(request, 'AgregarClinico.html')
            # Validación de formato de RUT (Ejemplo: 12345678-9)
            if not re.match(r'^\d{7,8}-[kK0-9]$', rut):
                messages.error(request, 'El RUT ingresado no es válido. Debe ser en formato 12345678-9.')
                return render(request, 'AgregarClinico.html')

            try:
                clinico = Clinico(
                    rut=rut,
                    nombre=nombre,
                    apellido=apellido,
                    profesion=profesion,
                    contraseña=contraseña
                )
                clinico.save()
                messages.success(request, 'Clínico agregado exitosamente.')
                return redirect('ver')

            except Exception as e:
                messages.error(request, f'Error al agregar el clínico: {e}')

        return render(request, 'AgregarClinico.html')

    return redirect('login')


def VerClinicos(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')  # Obtener el rut del clínico a eliminar
        if rut:
            clinico = Clinico.objects.get(rut=rut)
            clinico.delete()  # Eliminar al clínico
            messages.success(request, 'Clínico eliminado exitosamente.')
            return redirect('ver')  # Redirige después de eliminar

    # Obtener la lista actualizada de clínicos
    clinicos = Clinico.objects.all()
    return render(request, 'VerClinicos.html', {'clinicos': clinicos})

def EditarClinicos(request): 
    if request.method == 'POST': 
        rut = request.POST['rut']
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        profesion = request.POST['profesion']

        try:
            clinico = get_object_or_404(Clinico, rut=rut)
            clinico.nombre = nombre
            clinico.apellido = apellido
            clinico.profesion = profesion
            clinico.save()
            
          

        except Exception as e:
            messages.error(request, f'Error al editar el clínico: {e}')

        return redirect('ver') 

    return redirect('ver') 

    
    
