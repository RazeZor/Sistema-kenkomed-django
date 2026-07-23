# ciclo NOT NULL post-backfill

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SesionesKinesicas', '0006_ciclos_clinicos_inicial'),
        ('ciclos_clinicos', '0002_backfill_ciclos_existentes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sesionkinesica',
            name='ciclo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sesiones_kinesicas',
                to='ciclos_clinicos.cicloclinico',
            ),
        ),
        migrations.AlterField(
            model_name='registroescalasesion',
            name='ciclo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='registros_escalas_sesion',
                to='ciclos_clinicos.cicloclinico',
            ),
        ),
    ]
