from .models import MembresiaClinica

class ClinicaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'rut_clinico' in request.session:
            # Si ya hay una clínica seleccionada en sesión, podemos verificar que sigue siendo válida
            # o si no hay ninguna cargada, cargar la primera activa.
            if 'clinica_id' not in request.session:
                membresia = MembresiaClinica.objects.filter(
                    clinico_id=request.session['rut_clinico'],
                    activo=True
                ).first()
                if membresia:
                    request.session['clinica_id'] = membresia.clinica.id
                    request.session['clinica_nombre'] = membresia.clinica.nombre
                    request.session['es_admin_clinica'] = membresia.rol == 'admin'
        
        response = self.get_response(request)
        return response
