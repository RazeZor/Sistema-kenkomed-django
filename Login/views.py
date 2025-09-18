from django.contrib import messages
from django.shortcuts import redirect, render
from Login.models import Clinico

def validarLogin(request):
    try:
        if request.method == 'POST':
            rut = request.POST.get('rut')
            password = request.POST.get('password')
            recordar = request.POST.get('recordar')  # <-- checkbox del form

            try:
                clinico = Clinico.objects.get(rut=rut)
                print(f"Clínico encontrado: {clinico}")

                # Comprueba la contraseña
                if hasattr(clinico, 'check_password') and clinico.check_password(password):
                    # Guardar datos en sesión
                    request.session['rut_clinico'] = clinico.rut
                    request.session['nombre_clinico'] = f"{clinico.nombre} {clinico.apellido}"
                    request.session['es_admin'] = clinico.EsAdmin

                    # Control de "recordar"
                    if recordar:
                        request.session.set_expiry(60 * 60 * 24 * 30)
                    else:
                        # Expira al cerrar el navegador
                        request.session.set_expiry(0)

                    return redirect('panel')
                else:
                    messages.error(request, 'La contraseña ingresada es incorrecta.')
            except Clinico.DoesNotExist:
                messages.error(request, 'El RUT ingresado no está registrado.')
                print("Clínico no encontrado")
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
                print(f"Error inesperado: {str(e)}")

        return render(request, 'Login.html')
    
    except Exception as e:
        messages.error(request, f'Error inesperado: {str(e)}')
        return render(request, 'Login.html')