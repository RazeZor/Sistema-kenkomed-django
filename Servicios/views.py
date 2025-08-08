from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

# Create your views here.
def VerServicios(request):
    if request.method == 'POST':
        contrasenia_para_kinesiologos = '123'
        Contrasenia = request.POST.get('password')  # ← Usamos POST aquí

        if Contrasenia == contrasenia_para_kinesiologos:
            return redirect('login')
        else:
            return render(request, 'Servicios.html', {'error': 'Contraseña incorrecta'})
        
    return render(request, 'Servicios.html')
