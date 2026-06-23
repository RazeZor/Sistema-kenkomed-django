from django.db import migrations


def crear_clinicas_y_asignar_pacientes(apps, schema_editor):
    Clinico = apps.get_model('Login', 'Clinico')
    Paciente = apps.get_model('Login', 'Paciente')
    Clinica = apps.get_model('clinicas', 'Clinica')
    MembresiaClinica = apps.get_model('clinicas', 'MembresiaClinica')

    for clinico in Clinico.objects.all():
        clinica, _ = Clinica.objects.get_or_create(
            nombre=f"Consulta de {clinico.nombre} {clinico.apellido}",
            defaults={
                'tipo': 'individual',
                'max_clinicos': 1,
                'correo': clinico.correo,
                'ciudad': clinico.ciudad,
                'telefono': clinico.telefono,
            },
        )
        MembresiaClinica.objects.get_or_create(
            clinico=clinico,
            clinica=clinica,
            defaults={'rol': 'admin', 'activo': True},
        )

        for paciente in Paciente.objects.filter(clinico=clinico):
            paciente.clinica = clinica
            if not paciente.clinico_creador_id:
                paciente.clinico_creador = clinico
            paciente.save(update_fields=['clinica', 'clinico_creador'])


def revertir_migracion(apps, schema_editor):
    Paciente = apps.get_model('Login', 'Paciente')
    Paciente.objects.update(clinica=None, clinico_creador=None)


class Migration(migrations.Migration):

    dependencies = [
        ('clinicas', '0001_initial'),
        ('Login', '0065_delete_tiempo_paciente_clinica_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_clinicas_y_asignar_pacientes, revertir_migracion),
    ]
