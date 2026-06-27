from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0069_auditoria_acciones_sistema'),
    ]

    operations = [
        migrations.AddField(
            model_name='paciente',
            name='tipo_documento',
            field=models.CharField(
                choices=[
                    ('rut_chile', 'RUT chileno'),
                    ('pasaporte', 'Pasaporte'),
                    ('dni_extranjero', 'DNI / Documento extranjero'),
                    ('otro', 'Otro documento'),
                ],
                default='rut_chile',
                max_length=20,
                verbose_name='Tipo de documento',
            ),
        ),
        migrations.AddField(
            model_name='paciente',
            name='pais_documento',
            field=models.CharField(
                blank=True, default='', max_length=3, verbose_name='País emisión documento',
            ),
        ),
        migrations.AlterField(
            model_name='paciente',
            name='rut',
            field=models.CharField(
                max_length=32, primary_key=True, serialize=False, unique=True,
                verbose_name='Identificador',
            ),
        ),
    ]
