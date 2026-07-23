from clinicas.utils import paciente_pertenece_a_sesion


def ciclo_pertenece_a_sesion(request, ciclo):
    if not ciclo:
        return False
    if not paciente_pertenece_a_sesion(request, ciclo.paciente):
        return False
    clinica_id = request.session.get('clinica_id')
    if clinica_id and ciclo.clinica_id != clinica_id:
        return False
    return True
