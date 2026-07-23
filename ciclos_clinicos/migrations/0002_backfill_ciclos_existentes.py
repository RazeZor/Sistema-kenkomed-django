# Data migration — backfill CicloClinico for existing patients

from django.db import migrations


def crear_ciclos_desde_datos_existentes(apps, schema_editor):
    Paciente = apps.get_model('Login', 'Paciente')
    CicloClinico = apps.get_model('ciclos_clinicos', 'CicloClinico')
    formularioClinico = apps.get_model('Login', 'formularioClinico')
    SesionKinesica = apps.get_model('SesionesKinesicas', 'SesionKinesica')

    modelos_ciclo = [
        ('Login', 'formularioClinico', 'ciclo_id'),
        ('Login', 'CuestionarioPSFS', 'ciclo_id'),
        ('Login', 'Groc', 'ciclo_id'),
        ('Login', 'CuestionarioEQ_5D', 'ciclo_id'),
        ('Login', 'CuestionarioBarthel', 'ciclo_id'),
        ('Login', 'CuestionarioScrenning', 'ciclo_id'),
        ('Login', 'CuestionarioEvaluacionENA', 'ciclo_id'),
        ('SesionesKinesicas', 'SesionKinesica', 'ciclo_id'),
        ('SesionesKinesicas', 'RegistroEscalaSesion', 'ciclo_id'),
        ('TiposDeFormularios', 'EvaluacionLEFS', 'ciclo_id'),
        ('TiposDeFormularios', 'EvaluacionOswestry', 'ciclo_id'),
        ('TiposDeFormularios', 'EvaluacionQuickDASH', 'ciclo_id'),
        ('TiposDeFormularios', 'EvaluacionWOMAC', 'ciclo_id'),
    ]

    pacientes_con_datos = set()

    for app_label, model_name, _ in modelos_ciclo:
        Model = apps.get_model(app_label, model_name)
        for row in Model.objects.exclude(paciente_id__isnull=True).values_list('paciente_id', flat=True).distinct():
            if row:
                pacientes_con_datos.add(row)

    for paciente_id in pacientes_con_datos:
        try:
            paciente = Paciente.objects.get(pk=paciente_id)
        except Paciente.DoesNotExist:
            continue

        if not paciente.clinica_id:
            continue

        tiene_sesion_final = SesionKinesica.objects.filter(
            paciente_id=paciente_id,
            es_sesion_final=True,
        ).exists()

        estado = 'finalizado' if tiene_sesion_final else 'activo'

        ciclo, created = CicloClinico.objects.get_or_create(
            paciente_id=paciente_id,
            clinica_id=paciente.clinica_id,
            numero_ciclo=1,
            defaults={
                'estado': estado,
                'clinico_responsable_id': paciente.clinico_creador_id or paciente.clinico_id,
            },
        )

        if not created and ciclo.estado == 'activo' and tiene_sesion_final:
            ciclo.estado = 'finalizado'
            ciclo.save(update_fields=['estado'])

        for app_label, model_name, field in modelos_ciclo:
            Model = apps.get_model(app_label, model_name)
            Model.objects.filter(paciente_id=paciente_id, **{f'{field}__isnull': True}).update(**{field: ciclo.id})

        formularioClinico.objects.filter(paciente_id=paciente_id).update(ciclo_id=ciclo.id)


def revertir_ciclos(apps, schema_editor):
    CicloClinico = apps.get_model('ciclos_clinicos', 'CicloClinico')
    CicloClinico.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ciclos_clinicos', '0001_ciclos_clinicos_inicial'),
        ('Login', '0072_ciclos_clinicos_inicial'),
        ('SesionesKinesicas', '0006_ciclos_clinicos_inicial'),
        ('TiposDeFormularios', '0004_ciclos_clinicos_inicial'),
    ]

    operations = [
        migrations.RunPython(crear_ciclos_desde_datos_existentes, revertir_ciclos),
    ]
