from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0065_delete_tiempo_paciente_clinica_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='reserva',
            index=models.Index(fields=['clinico', 'fecha'], name='Login_reser_clinico_8a1f2d_idx'),
        ),
        migrations.AddIndex(
            model_name='reserva',
            index=models.Index(fields=['fecha', 'hora_inicio'], name='Login_reser_fecha_h_4c9e81_idx'),
        ),
    ]
