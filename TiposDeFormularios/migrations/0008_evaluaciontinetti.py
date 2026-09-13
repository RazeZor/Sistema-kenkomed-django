# Generated manually — EvaluacionTinetti

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0069_auditoria_acciones_sistema'),
        ('TiposDeFormularios', '0007_evaluacionberg'),
        ('ciclos_clinicos', '0002_backfill_ciclos_existentes'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionTinetti',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_evaluacion', models.DateTimeField(auto_now_add=True)),
                ('eq_01_sentado', models.IntegerField(help_text='Equilibrio sentado (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('eq_02_levantarse', models.IntegerField(help_text='Levantarse (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('eq_03_intentos', models.IntegerField(help_text='Intentos para levantarse (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('eq_04_equi_inmediato', models.IntegerField(help_text='Equilibrio inmediato primeros 5s (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('eq_05_equi_bipedestacion', models.IntegerField(help_text='Equilibrio en bipedestación (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('eq_06_empujon', models.IntegerField(help_text='Empujón tórax 3 veces (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('eq_07_ojos_cerrados', models.IntegerField(help_text='Ojos cerrados pies juntos (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('eq_08_giro_360', models.IntegerField(help_text='Giro 360 grados (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('eq_09_sentarse', models.IntegerField(help_text='Sentarse (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('ma_01_iniciacion', models.IntegerField(help_text='Iniciación de la marcha (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('ma_02_longitud_altura', models.IntegerField(help_text='Longitud y altura del paso (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('ma_03_simetria', models.IntegerField(help_text='Simetría del paso (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('ma_04_continuidad', models.IntegerField(help_text='Continuidad de los pasos (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('ma_05_trayectoria', models.IntegerField(help_text='Trayectoria (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('ma_06_tronco', models.IntegerField(help_text='Tronco (0-2)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(2)])),
                ('ma_07_postura_marcha', models.IntegerField(help_text='Postura al caminar (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('notas_clinicas', models.TextField(blank=True, null=True)),
                ('ciclo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_tinetti',
                    to='ciclos_clinicos.cicloclinico',
                )),
                ('clinico', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_tinetti',
                    to='Login.clinico',
                )),
                ('paciente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='evaluaciones_tinetti',
                    to='Login.paciente',
                )),
            ],
            options={
                'verbose_name': 'Evaluación Tinetti',
                'verbose_name_plural': 'Evaluaciones Tinetti',
                'ordering': ['-fecha_evaluacion'],
            },
        ),
    ]
