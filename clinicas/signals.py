from Login.models import Clinico

from .models import Clinica, MembresiaClinica


def crear_clinica_individual(clinico):
    clinica = Clinica.objects.create(
        nombre=f"Consulta de {clinico.nombre} {clinico.apellido}",
        tipo='individual',
        max_clinicos=1,
        correo=clinico.correo,
        ciudad=clinico.ciudad,
        telefono=clinico.telefono,
    )
    MembresiaClinica.objects.create(
        clinico=clinico,
        clinica=clinica,
        rol='admin',
        activo=True,
    )
    return clinica

