# Generated manually — EvaluacionTUG

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0069_auditoria_acciones_sistema'),
        ('TiposDeFormularios', '0005_ciclo_not_null'),
        ('ciclos_clinicos', '0002_backfill_ciclos_existentes'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionTUG',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_evaluacion', models.DateTimeField(auto_now_add=True)),
                ('tiempo_segundos', models.FloatField(
                    help_text='Tiempo en segundos que tardó el paciente en completar el test',
                    validators=[django.core.validators.MinValueValidator(0)],
                )),
                ('usa_ayuda_marcha', models.BooleanField(
                    default=False,
                    help_text='El paciente utilizó dispositivo de ayuda durante el test',
                )),
                ('observaciones', models.JSONField(
                    blank=True,
                    default=list,
                    help_text='Lista de observaciones clínicas marcadas durante el test',
                )),
                ('notas_clinicas', models.TextField(blank=True, null=True)),
                ('ciclo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_tug',
                    to='ciclos_clinicos.cicloclinico',
                )),
                ('clinico', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_tug',
                    to='Login.clinico',
                )),
                ('paciente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_tug',
                    to='Login.paciente',
                )),
            ],
            options={
                'verbose_name': 'Evaluación TUG',
                'verbose_name_plural': 'Evaluaciones TUG',
                'ordering': ['-fecha_evaluacion'],
            },
        ),
    ]
