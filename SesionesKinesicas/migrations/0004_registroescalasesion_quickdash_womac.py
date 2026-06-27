from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('SesionesKinesicas', '0003_registroescalasesion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registroescalasesion',
            name='tipo_escala',
            field=models.CharField(
                choices=[
                    ('psfs', 'PSFS'),
                    ('groc', 'GROC'),
                    ('eq5d', 'EQ-5D'),
                    ('barthel', 'Barthel'),
                    ('ena', 'ENA'),
                    ('screening', 'Screening Örebro'),
                    ('oswestry', 'Oswestry ODI'),
                    ('lefs', 'LEFS'),
                    ('quickdash', 'QuickDASH'),
                    ('womac', 'WOMAC'),
                ],
                max_length=20,
            ),
        ),
    ]
