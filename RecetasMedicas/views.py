from django.shortcuts import render, redirect
from django.contrib import messages
from Login.models import Paciente, Clinico, RecetaMedica

def renderizar_html_receta(request):
    # --- Verificar sesión ---
    if 'nombre_clinico' not in request.session:
        messages.error(request, 'Debes iniciar sesión para acceder a esta página.')
        return redirect('login')

    rut_clinico = request.session.get('rut_clinico')
    nombre_clinico = request.session.get('nombre_clinico')
    es_admin = request.session.get('es_admin', False)

    # Obtener clínico logueado
    clinico = Clinico.objects.filter(rut=rut_clinico).first()
    if not clinico:
        messages.error(request, 'No se encontró el clínico en el sistema.')
        return redirect('login')

    paciente = None
    receta = None
    error = None
    mensaje = None
    mostrar_formulario = False

    # --- Manejo de POST ---
    if request.method == 'POST':
        rut = request.POST.get('rutsito', '').strip()
        accion = request.POST.get('accion', '').lower()

        try:
            # Buscar paciente por RUT
            paciente_encontrado = Paciente.objects.get(rut=rut)
            if not es_admin and paciente_encontrado.clinico != clinico:
                paciente = None
                receta = None
                error = "No se encontró ningún paciente con ese RUT o no tienes permisos para verlo."
            else:
                paciente = paciente_encontrado
                receta = RecetaMedica.objects.filter(paciente=paciente).first()
                if accion == 'crear':
                    if receta:
                        mensaje = "El paciente ya tiene una receta registrada."
                    else:
                        RecetaMedica.objects.create(
                            paciente=paciente,
                            clinico=clinico,
                            medicamentos=request.POST.get('medicamentos', '').strip(),
                            indicaciones=request.POST.get('indicaciones', '').strip(),
                            NotaRecetaMedica=request.POST.get('notas', '').strip()
                        )
                        mensaje = "Receta médica creada exitosamente."
                        receta = RecetaMedica.objects.get(paciente=paciente)
                elif accion == 'editar':
                    if receta:
                        receta.medicamentos = request.POST.get('medicamentos', '').strip()
                        receta.indicaciones = request.POST.get('indicaciones', '').strip()
                        receta.NotaRecetaMedica = request.POST.get('notas', '').strip()
                        receta.save()
                        mensaje = "Receta médica actualizada correctamente."
                    else:
                        error = "No existe una receta para editar."
                elif accion == 'eliminar':
                    if receta:
                        receta.delete()
                        mensaje = "Receta médica eliminada correctamente."
                        receta = None
                    else:
                        error = "No existe receta para eliminar."
        except Paciente.DoesNotExist:
            paciente = None
            receta = None
            error = "No se encontró ningún paciente con ese RUT o no tienes permisos para verlo."

    # --- Manejo de GET ---
    elif request.method == 'GET':
        rut = request.GET.get('rut', '').strip()
        accion = request.GET.get('accion', '').lower()

        if rut:
            try:
                paciente_encontrado = Paciente.objects.get(rut=rut)
                if not es_admin and paciente_encontrado.clinico != clinico:
                    paciente = None
                    receta = None
                    error = "No se encontró ningún paciente con ese RUT o no tienes permisos para verlo."
                else:
                    paciente = paciente_encontrado
                    receta = RecetaMedica.objects.filter(paciente=paciente).first()
                    if accion in ['nueva', 'editar']:
                        mostrar_formulario = True
            except Paciente.DoesNotExist:
                paciente = None
                receta = None
                error = "No se encontró ningún paciente con ese RUT o no tienes permisos para verlo."

    return render(request, 'agregar_receta.html', {
        'paciente': paciente,
        'receta': receta,
        'error': error,
        'mensaje': mensaje,
        'mostrar_formulario': mostrar_formulario
    })
                                    
