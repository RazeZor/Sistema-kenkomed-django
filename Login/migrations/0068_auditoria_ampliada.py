from django.db import migrations, models
import django.db.models.deletion


ACCIONES_NUEVAS = [
    ('consulta_historial', 'Consultó historial clínico'),
    ('edicion_nota_clinica', 'Editó notas clínicas del historial'),
    ('consulta_informe_dss', 'Visualizó informe DSS (anamnesis)'),
    ('consulta_ficha_profesional', 'Visualizó ficha clínica profesional'),
    ('consulta_resumen_paciente', 'Visualizó resumen del paciente en panel'),
    ('alta_paciente', 'Registró nuevo paciente'),
    ('edicion_paciente', 'Modificó datos demográficos del paciente'),
    ('eliminacion_paciente', 'Eliminó ficha de paciente'),
    ('exportacion_arco_json', 'Exportó ficha completa (ARCO — JSON)'),
    ('exportacion_arco_html', 'Exportó ficha completa (ARCO — HTML)'),
    ('reserva_crear', 'Creó cita / reserva'),
    ('reserva_modificar', 'Modificó cita / reserva'),
    ('reserva_eliminar', 'Eliminó cita / reserva'),
    ('exportacion_auditoria_pdf', 'Exportó registro de auditoría (PDF)'),
]

MAPA_ACCIONES = {
    'historial': 'consulta_historial',
    'informe': 'consulta_informe_dss',
    'ficha': 'consulta_ficha_profesional',
    'exportar_json': 'exportacion_arco_json',
    'exportar_html': 'exportacion_arco_html',
}


def migrar_codigos_accion(apps, schema_editor):
    AuditoriaAcceso = apps.get_model('Login', 'AuditoriaAcceso')
    for viejo, nuevo in MAPA_ACCIONES.items():
        AuditoriaAcceso.objects.filter(accion=viejo).update(accion=nuevo)


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0067_auditoriaacceso_and_more'),
        ('clinicas', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditoriaacceso',
            name='paciente',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='auditorias_acceso',
                to='Login.paciente',
            ),
        ),
        migrations.AddField(
            model_name='auditoriaacceso',
            name='detalle',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='auditoriaacceso',
            name='es_admin_sistema',
            field=models.BooleanField(default=False, verbose_name='Admin KenkoMed'),
        ),
        migrations.AddField(
            model_name='auditoriaacceso',
            name='es_admin_centro',
            field=models.BooleanField(default=False, verbose_name='Admin del centro'),
        ),
        migrations.AlterField(
            model_name='auditoriaacceso',
            name='accion',
            field=models.CharField(choices=ACCIONES_NUEVAS, max_length=40),
        ),
        migrations.RunPython(migrar_codigos_accion, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name='auditoriaacceso',
            index=models.Index(fields=['clinico', '-fecha'], name='Login_audit_clinico_fecha_idx'),
        ),
        migrations.AlterModelOptions(
            name='auditoriaacceso',
            options={
                'ordering': ['-fecha'],
                'verbose_name': 'Registro de auditoría clínica',
                'verbose_name_plural': 'Registros de auditoría clínica',
            },
        ),
    ]
