from django.db import migrations, models


ACCIONES_COMPLETAS = [
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
    ('consulta_cuestionario', 'Consultó cuestionario clínico'),
    ('edicion_cuestionario', 'Editó cuestionario clínico'),
    ('consulta_lista_sesiones_kine', 'Consultó listado de sesiones kinésicas'),
    ('consulta_sesion_kine', 'Visualizó sesión kinésica'),
    ('alta_sesion_kine', 'Registró sesión kinésica'),
    ('edicion_sesion_kine', 'Editó sesión kinésica'),
    ('consulta_receta', 'Consultó receta médica'),
    ('receta_crear', 'Creó receta médica'),
    ('receta_editar', 'Editó receta médica'),
    ('receta_eliminar', 'Eliminó receta médica'),
    ('consulta_estadisticas_centro', 'Consultó estadísticas del centro'),
    ('consulta_estadisticas_paciente', 'Consultó estadísticas del paciente'),
    ('consulta_calendario', 'Consultó agenda / calendario'),
    ('consulta_lista_pacientes', 'Consultó listado de pacientes'),
    ('qr_generar', 'Generó formulario remoto (QR)'),
    ('qr_desactivar', 'Desactivó formulario remoto (QR)'),
    ('consulta_auditoria', 'Consultó registro de auditoría'),
    ('edicion_anamnesis', 'Registró o editó anamnesis DSS'),
    ('formulario_qr_enviado', 'Paciente envió anamnesis vía formulario QR'),
    ('consulta_formulario_inicial', 'Accedió al formulario de anamnesis DSS'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('Login', '0068_auditoria_ampliada'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditoriaacceso',
            name='accion',
            field=models.CharField(choices=ACCIONES_COMPLETAS, max_length=40),
        ),
    ]
