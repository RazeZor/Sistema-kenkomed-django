from django.contrib import messages
from django.shortcuts import redirect, render

from Login.models import Clinico
from ProyectoMainAPP.decorators.login_requerido import requiere_clinico
from clinicas.models import MembresiaClinica
from clinicas.utils import (
    filtrar_pacientes_por_sesion,
    obtener_clinica_de_sesion,
    obtener_membresias_del_centro,
)


@requiere_clinico
def RenderizarPerfil(request):
    rut_clinico = request.session.get('rut_clinico')
    perfil = Clinico.objects.filter(rut=rut_clinico).first()

    if not perfil:
        messages.error(request, 'Perfil no encontrado.')
        return redirect('login')

    if request.method == 'POST':
        try:
            perfil.correo = request.POST.get('correo', perfil.correo or '').strip() or None
            perfil.telefono = request.POST.get('telefono', perfil.telefono or '').strip() or None
            perfil.centro_trabajo = request.POST.get('centro_trabajo', perfil.centro_trabajo or '').strip() or None
            perfil.ciudad = request.POST.get('ciudad', perfil.ciudad or '').strip() or None
            perfil.especialidad = request.POST.get('especialidad', perfil.especialidad or '').strip() or None
            perfil.numero_registro = request.POST.get('numero_registro', perfil.numero_registro or '').strip() or None
            perfil.descripcion = request.POST.get('descripcion', perfil.descripcion or '').strip() or None

            experiencia = request.POST.get('experiencia', '').strip()
            if experiencia:
                perfil.experiencia = int(experiencia)
            else:
                perfil.experiencia = None

            perfil.save()
            messages.success(request, 'Perfil actualizado correctamente.')
        except ValueError:
            messages.error(request, 'Años de experiencia debe ser un número válido.')
        except Exception as exc:
            messages.error(request, f'Error al actualizar el perfil: {exc}')

    clinica = obtener_clinica_de_sesion(request)
    membresia = (
        MembresiaClinica.objects.filter(clinico=perfil, activo=True)
        .select_related('clinica')
        .first()
    )
    if not clinica and membresia:
        clinica = membresia.clinica

    pacientes_atendidos = filtrar_pacientes_por_sesion(request).count()
    total_miembros = obtener_membresias_del_centro(request).count() if clinica else 0

    return render(request, 'perfil.html', {
        'nombre_clinico': f'{perfil.nombre} {perfil.apellido}',
        'pacientesAtendidos': pacientes_atendidos,
        'perfil': perfil,
        'clinica': clinica,
        'membresia': membresia,
        'total_miembros': total_miembros,
        'es_admin': request.session.get('es_admin', False),
        'es_admin_clinica': request.session.get('es_admin_clinica', False),
        'es_centro_compartido': bool(clinica and clinica.tipo == 'clinica'),
    })
