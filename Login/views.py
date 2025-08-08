from django.contrib import messages
from django.shortcuts import redirect, render
from Login.models import Clinico


def validarLogin(request):
    if request.method == 'POST':
        rut = request.POST.get('rut')
        password = request.POST.get('password')  # Cambiado a 'password' para coincidir con el formulario
        try:
            clinico = Clinico.objects.get(rut=rut)
            print(f"Clínico encontrado: {clinico}")
            print(f"Contraseña almacenada: {clinico.contraseña}")
            
            if clinico.contraseña == password:
                request.session['rut_clinico'] = clinico.rut
                request.session['nombre_clinico'] = f"{clinico.nombre} {clinico.apellido}"
                if clinico.EsAdmin:
                        print("Es administrador")
                        request.session['es_admin'] = True
                        
                        return redirect('panel')
                else:
                    print("No es administrador")
                    request.session['es_admin'] = False
                    return redirect('panel')
            else:
                messages.error(request, 'La contraseña ingresada es incorrecta.')
                print("Contraseña incorrecta")
        except Clinico.DoesNotExist:
            messages.error(request, 'El RUT ingresado no está registrado.')
            print("Clínico no encontrado")
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
            print(f"Error inesperado: {str(e)}")
  
        
    
    return render(request, 'Login.html')



