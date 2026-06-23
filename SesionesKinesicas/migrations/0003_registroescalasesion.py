from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0069_auditoria_acciones_sistema'),
        ('SesionesKinesicas', '0002_sesionkinesica_diagnostico_final_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistroEscalaSesion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_escala', models.CharField(choices=[('psfs', 'PSFS'), ('groc', 'GROC'), ('eq5d', 'EQ-5D'), ('barthel', 'Barthel'), ('ena', 'ENA'), ('screening', 'Screening Örebro'), ('oswestry', 'Oswestry ODI'), ('lefs', 'LEFS')], max_length=20)),
                ('resumen', models.CharField(max_length=255)),
                ('url_name', models.CharField(blank=True, default='', max_length=40)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_escalas_sesion', to='Login.paciente')),
                ('sesion_kinesica', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_escalas', to='SesionesKinesicas.sesionkinesica')),
            ],
            options={
                'verbose_name': 'Escala aplicada en sesión',
                'verbose_name_plural': 'Escalas aplicadas en sesiones',
                'ordering': ['-fecha_registro'],
            },
        ),
        migrations.AddIndex(
            model_name='registroescalasesion',
            index=models.Index(fields=['paciente', '-fecha_registro'], name='SesionesKin_pacient_8f0a2a_idx'),
        ),
        migrations.AddIndex(
            model_name='registroescalasesion',
            index=models.Index(fields=['sesion_kinesica', '-fecha_registro'], name='SesionesKin_sesion__a1b3c4_idx'),
        ),
    ]
