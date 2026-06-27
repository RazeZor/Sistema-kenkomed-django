# Generated manually

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0069_auditoria_acciones_sistema'),
        ('TiposDeFormularios', '0002_evaluacionlefs'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluacionQuickDASH',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_evaluacion', models.DateTimeField(auto_now_add=True)),
                ('notas_clinicas', models.TextField(blank=True, null=True)),
                ('pregunta_1', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_2', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_3', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_4', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_5', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_6', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_7', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_8', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_9', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_10', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('pregunta_11', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('clinico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluaciones_quickdash', to='Login.clinico')),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluaciones_quickdash', to='Login.paciente')),
            ],
            options={
                'verbose_name': 'Evaluación QuickDASH',
                'verbose_name_plural': 'Evaluaciones QuickDASH',
                'ordering': ['-fecha_evaluacion'],
            },
        ),
        migrations.CreateModel(
            name='EvaluacionWOMAC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_evaluacion', models.DateTimeField(auto_now_add=True)),
                ('respuestas', models.JSONField(help_text='Lista de 24 enteros (0–4) en orden WOMAC')),
                ('notas_clinicas', models.TextField(blank=True, null=True)),
                ('clinico', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluaciones_womac', to='Login.clinico')),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluaciones_womac', to='Login.paciente')),
            ],
            options={
                'verbose_name': 'Evaluación WOMAC',
                'verbose_name_plural': 'Evaluaciones WOMAC',
                'ordering': ['-fecha_evaluacion'],
            },
        ),
    ]
