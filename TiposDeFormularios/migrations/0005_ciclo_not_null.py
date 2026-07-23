# ciclo NOT NULL post-backfill

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('TiposDeFormularios', '0004_ciclos_clinicos_inicial'),
        ('ciclos_clinicos', '0002_backfill_ciclos_existentes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evaluacionlefs',
            name='ciclo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evaluaciones_lefs',
                to='ciclos_clinicos.cicloclinico',
            ),
        ),
        migrations.AlterField(
            model_name='evaluacionoswestry',
            name='ciclo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evaluaciones_oswestry',
                to='ciclos_clinicos.cicloclinico',
            ),
        ),
        migrations.AlterField(
            model_name='evaluacionquickdash',
            name='ciclo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evaluaciones_quickdash',
                to='ciclos_clinicos.cicloclinico',
            ),
        ),
        migrations.AlterField(
            model_name='evaluacionwomac',
            name='ciclo',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evaluaciones_womac',
                to='ciclos_clinicos.cicloclinico',
            ),
        ),
    ]
