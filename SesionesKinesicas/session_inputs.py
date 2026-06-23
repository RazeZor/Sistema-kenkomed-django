"""Recolección y validación de campos de texto de sesiones kinésicas."""
from ProyectoMainAPP.text_validation import validar_campos_texto_plano

EVALUACION_INICIAL_KEYS = (
    'motivo_consulta', 'causa_lesion', 'mecanismo_lesion', 'manejo_abordaje',
    'fecha_lesion', 'fecha_control_medico', 'alteraciones_funcionales', 'objetivo_paciente',
    'dolor_presente', 'dolor_antiguedad', 'dolor_localizacion', 'dolor_intensidad',
    'dolor_caracteristicas', 'dolor_irradiacion',
    'postura_plano_frontal_anterior', 'postura_plano_frontal_posterior', 'postura_plano_sagital',
    'examen_observacion', 'examen_inspeccion', 'examen_palpacion',
    'rango_activo_conservados', 'rango_activo_limitados',
    'rango_pasivo_mmss_derecha', 'rango_pasivo_mmss_izquierda',
    'rango_pasivo_mmii_derecha', 'rango_pasivo_mmii_izquierda',
    'funcion_muscular_superiores', 'funcion_muscular_inferiores',
    'movimiento_squat_overhead', 'movimiento_single_leg_squat', 'movimiento_drop_test',
    'movimiento_salto_cajon', 'movimiento_carga_squat_press', 'movimiento_carga_split_deadlift',
    'movimiento_carga_turkish_get_up', 'test_ortopedicos',
)

ETIQUETAS_CAMPOS = {
    'motivo_consulta': 'Motivo de consulta',
    'causa_lesion': 'Causa de la lesión',
    'mecanismo_lesion': 'Mecanismo de lesión',
    'manejo_abordaje': 'Manejo y abordaje previo',
    'fecha_lesion': 'Fecha de lesión',
    'fecha_control_medico': 'Fecha control médico',
    'alteraciones_funcionales': 'Alteraciones funcionales',
    'objetivo_paciente': 'Objetivo del paciente',
    'dolor_presente': 'Dolor presente',
    'dolor_antiguedad': 'Antigüedad del dolor',
    'dolor_localizacion': 'Localización del dolor',
    'dolor_intensidad': 'Intensidad del dolor',
    'dolor_caracteristicas': 'Características del dolor',
    'dolor_irradiacion': 'Irradiación del dolor',
    'postura_plano_frontal_anterior': 'Postura frontal anterior',
    'postura_plano_frontal_posterior': 'Postura frontal posterior',
    'postura_plano_sagital': 'Postura plano sagital',
    'examen_observacion': 'Examen — observación',
    'examen_inspeccion': 'Examen — inspección',
    'examen_palpacion': 'Examen — palpación',
    'rango_activo_conservados': 'Rango activo conservados',
    'rango_activo_limitados': 'Rango activo limitados',
    'rango_pasivo_mmss_derecha': 'Rango pasivo MMSS derecha',
    'rango_pasivo_mmss_izquierda': 'Rango pasivo MMSS izquierda',
    'rango_pasivo_mmii_derecha': 'Rango pasivo MMII derecha',
    'rango_pasivo_mmii_izquierda': 'Rango pasivo MMII izquierda',
    'funcion_muscular_superiores': 'Función muscular superiores',
    'funcion_muscular_inferiores': 'Función muscular inferiores',
    'movimiento_squat_overhead': 'Squat overhead',
    'movimiento_single_leg_squat': 'Single leg squat',
    'movimiento_drop_test': 'Drop test',
    'movimiento_salto_cajon': 'Salto al cajón',
    'movimiento_carga_squat_press': 'Squat press con carga',
    'movimiento_carga_split_deadlift': 'Split deadlift con carga',
    'movimiento_carga_turkish_get_up': 'Turkish get up con carga',
    'test_ortopedicos': 'Test ortopédicos',
    'notas_clinicas': 'Notas clínicas',
    'evolucion': 'Evolución',
    'diagnostico_final': 'Diagnóstico kinésico final',
    'resumen_tratamiento': 'Resumen del tratamiento',
    'logros_obtenidos': 'Logros obtenidos',
    'estado_al_alta': 'Estado al alta',
    'recomendaciones_alta': 'Recomendaciones al alta',
    'plan_seguimiento': 'Plan de seguimiento',
}


def evaluacion_inicial_desde_post(post) -> dict:
    return {clave: post.get(clave, '') for clave in EVALUACION_INICIAL_KEYS}


def campos_texto_sesion_desde_post(post, *, incluir_evaluacion=False, incluir_final=False) -> dict:
    campos = {
        'notas_clinicas': post.get('notas_clinicas', ''),
        'evolucion': post.get('evolucion', ''),
    }
    if incluir_evaluacion:
        campos.update(evaluacion_inicial_desde_post(post))
    if incluir_final:
        campos.update({
            'diagnostico_final': post.get('diagnostico_final', ''),
            'resumen_tratamiento': post.get('resumen_tratamiento', ''),
            'logros_obtenidos': post.get('logros_obtenidos', ''),
            'estado_al_alta': post.get('estado_al_alta', ''),
            'recomendaciones_alta': post.get('recomendaciones_alta', ''),
            'plan_seguimiento': post.get('plan_seguimiento', ''),
        })
    return campos


def validar_post_sesion_kinesica(post, *, incluir_evaluacion=False, incluir_final=False) -> list[str]:
    """Retorna errores de validación; lista vacía = OK."""
    campos = campos_texto_sesion_desde_post(
        post,
        incluir_evaluacion=incluir_evaluacion,
        incluir_final=incluir_final,
    )
    return validar_campos_texto_plano(campos, ETIQUETAS_CAMPOS)
