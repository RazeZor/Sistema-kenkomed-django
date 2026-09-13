# Generated manually — EvaluacionBerg

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0069_auditoria_acciones_sistema'),
        ('TiposDeFormularios', '0006_evaluaciontug'),
        ('ciclos_clinicos', '0002_backfill_ciclos_existentes'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionBerg',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_evaluacion', models.DateTimeField(auto_now_add=True)),
                ('item_01', models.IntegerField(help_text='1. Sedestación a bipedestación (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_02', models.IntegerField(help_text='2. Bipedestación sin ayuda 2 min (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_03', models.IntegerField(help_text='3. Sedestación sin apoyar espalda 2 min (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_04', models.IntegerField(help_text='4. Bipedestación a sedestación (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_05', models.IntegerField(help_text='5. Transferencias (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_06', models.IntegerField(help_text='6. Bipedestación ojos cerrados 10s (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_07', models.IntegerField(help_text='7. Bipedestación pies juntos 1 min (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_08', models.IntegerField(help_text='8. Brazo extendido hacia delante (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_09', models.IntegerField(help_text='9. Recoger objeto del suelo (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_10', models.IntegerField(help_text='10. Girarse para mirar atrás (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_11', models.IntegerField(help_text='11. Girar 360 grados (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_12', models.IntegerField(help_text='12. Subir pies al escalón alternante (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_13', models.IntegerField(help_text='13. Pies en tándem (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('item_14', models.IntegerField(help_text='14. Bipedestación sobre un pie (0-4)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(4)])),
                ('notas_clinicas', models.TextField(blank=True, null=True)),
                ('ciclo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_berg',
                    to='ciclos_clinicos.cicloclinico',
                )),
                ('clinico', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_berg',
                    to='Login.clinico',
                )),
                ('paciente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_berg',
                    to='Login.paciente',
                )),
            ],
            options={
                'verbose_name': 'Evaluación Berg',
                'verbose_name_plural': 'Evaluaciones Berg',
                'ordering': ['-fecha_evaluacion'],
            },
        ),
    ]
