"""Helpers de plantilla y URL para ciclos clínicos."""


def contexto_ciclo_para_template(ciclo, paciente):
    qs = f'&ciclo_id={ciclo.id}' if ciclo else ''
    rut_qs = f'rut={paciente.rut}' if paciente else ''
    sep = '&' if rut_qs and qs else ''
    return {
        'ciclo': ciclo,
        'ciclo_id': ciclo.id if ciclo else None,
        'ciclo_solo_lectura': ciclo.es_solo_lectura if ciclo else False,
        'ciclo_query': f'{rut_qs}{sep}{qs.lstrip("&")}' if rut_qs or qs else '',
        'ciclo_query_amp': qs,
    }
