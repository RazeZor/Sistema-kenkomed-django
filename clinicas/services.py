from django.db import transaction

from Login.models import Clinico, Paciente

from .models import Clinica, MembresiaClinica


class ClinicaServiceError(Exception):
    pass


def contar_miembros_activos(clinica):
    return MembresiaClinica.objects.filter(clinica=clinica, activo=True).count()


def convertir_a_centro(clinica, nombre=None, max_clinicos=10):
    """Convierte una clínica individual en centro compartido."""
    clinica.tipo = 'clinica'
    if nombre:
        clinica.nombre = nombre
    clinica.max_clinicos = max(max_clinicos, contar_miembros_activos(clinica))
    clinica.save(update_fields=['tipo', 'nombre', 'max_clinicos'])
    return clinica


@transaction.atomic
def unir_clinico_a_centro(
    clinico_rut,
    clinica_destino_id,
    rol='miembro',
    migrar_pacientes=True,
    desactivar_clinica_anterior=True,
):
    """
    Une un clínico a un centro compartido.
    Opcionalmente migra sus pacientes y desactiva su clínica individual anterior.
    """
    try:
        clinico = Clinico.objects.get(rut=clinico_rut)
    except Clinico.DoesNotExist as exc:
        raise ClinicaServiceError(f'No existe un clínico con RUT {clinico_rut}') from exc

    try:
        clinica_destino = Clinica.objects.get(id=clinica_destino_id, activa=True)
    except Clinica.DoesNotExist as exc:
        raise ClinicaServiceError(f'No existe una clínica activa con id {clinica_destino_id}') from exc

    membresia_actual = (
        MembresiaClinica.objects.filter(clinico=clinico, activo=True)
        .select_related('clinica')
        .first()
    )

    if membresia_actual and membresia_actual.clinica_id == clinica_destino.id:
        return {
            'clinico': clinico,
            'clinica': clinica_destino,
            'membresia': membresia_actual,
            'pacientes_migrados': 0,
            'ya_estaba': True,
        }

    miembros_actuales = contar_miembros_activos(clinica_destino)
    if miembros_actuales >= clinica_destino.max_clinicos:
        raise ClinicaServiceError(
            f'El centro "{clinica_destino.nombre}" alcanzó el límite de '
            f'{clinica_destino.max_clinicos} profesionales.'
        )

    clinica_anterior = membresia_actual.clinica if membresia_actual else None
    pacientes_migrados = 0

    if migrar_pacientes and clinica_anterior and clinica_anterior.id != clinica_destino.id:
        pacientes_migrados = Paciente.objects.filter(clinica_id=clinica_anterior.id).update(
            clinica_id=clinica_destino.id
        )

    if membresia_actual:
        membresia_actual.activo = False
        membresia_actual.save(update_fields=['activo'])

    membresia, _ = MembresiaClinica.objects.update_or_create(
        clinico=clinico,
        clinica=clinica_destino,
        defaults={'rol': rol, 'activo': True},
    )

    if clinica_destino.tipo == 'individual' or clinica_destino.max_clinicos <= 1:
        convertir_a_centro(clinica_destino, max_clinicos=max(clinica_destino.max_clinicos, 10))

    if desactivar_clinica_anterior and clinica_anterior and clinica_anterior.id != clinica_destino.id:
        quedan_miembros = contar_miembros_activos(clinica_anterior)
        if quedan_miembros == 0 and clinica_anterior.tipo == 'individual':
            sin_pacientes = not Paciente.objects.filter(clinica_id=clinica_anterior.id).exists()
            if sin_pacientes:
                MembresiaClinica.objects.filter(clinica=clinica_anterior).delete()
                clinica_anterior.delete()
            else:
                clinica_anterior.activa = False
                clinica_anterior.save(update_fields=['activa'])

    return {
        'clinico': clinico,
        'clinica': clinica_destino,
        'membresia': membresia,
        'pacientes_migrados': pacientes_migrados,
        'ya_estaba': False,
    }
