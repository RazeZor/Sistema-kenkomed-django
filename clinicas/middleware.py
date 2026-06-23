from .models import MembresiaClinica

class ClinicaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'rut_clinico' in request.session:
            # Sincronizar siempre la clínica activa desde la membresía (un clínico = un centro).
            membresia = (
                MembresiaClinica.objects.filter(
                    clinico_id=request.session['rut_clinico'],
                    activo=True,
                )
                .select_related('clinica')
                .first()
            )
            if membresia and membresia.clinica.activa:
                request.session['clinica_id'] = membresia.clinica.id
                request.session['clinica_nombre'] = membresia.clinica.nombre
                request.session['es_admin_clinica'] = membresia.rol == 'admin'
            else:
                request.session.pop('clinica_id', None)
                request.session.pop('clinica_nombre', None)
                request.session['es_admin_clinica'] = False

        response = self.get_response(request)
        return response
