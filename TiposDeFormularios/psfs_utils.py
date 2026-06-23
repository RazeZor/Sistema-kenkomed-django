"""Utilidades para normalizar puntajes y sesiones PSFS."""
import json


def parse_psfs_json_field(value):
    """Convierte un JSONField PSFS (lista, str legacy o número) a lista de floats."""
    if value is None:
        return []

    while isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                return [round(float(value), 1)]
            except (TypeError, ValueError):
                return []

    if isinstance(value, (int, float)):
        return [round(float(value), 1)]

    if isinstance(value, list):
        result = []
        for item in value:
            if item is None or item == '':
                continue
            try:
                result.append(round(float(item), 1))
            except (TypeError, ValueError):
                continue
        return result

    return []


def compute_psfs_total(p1, p2, p3, stored_total=None):
    """Promedio de las 3 actividades (escala 0–10). Ignora totales corruptos > 10."""
    scores = []
    for s in (p1, p2, p3):
        if s is None or s == '':
            continue
        try:
            scores.append(float(s))
        except (TypeError, ValueError):
            continue
    if not scores:
        return 0.0
    avg = round(sum(scores) / len(scores), 1)
    return max(0.0, min(10.0, avg))


def normalize_single_session(nuevos):
    """Una sesión: siempre recalcula el total como promedio de las 3 actividades."""
    a1 = nuevos.get('actividad_1', [])
    a2 = nuevos.get('actividad_2', [])
    a3 = nuevos.get('actividad_3', [])
    if not (a1 and a2 and a3):
        return nuevos
    s1, s2, s3 = a1[-1], a2[-1], a3[-1]
    total = compute_psfs_total(s1, s2, s3)
    return {
        'actividad_1': [s1],
        'actividad_2': [s2],
        'actividad_3': [s3],
        'total': [total],
    }


def _display_score(value):
    if value is None:
        return 0
    if float(value) == int(float(value)):
        return int(value)
    return round(float(value), 1)


def build_psfs_sessions(cuestionario):
    """Lista de sesiones con claves alineadas al template y al gráfico."""
    if not cuestionario:
        return []

    p1_list = parse_psfs_json_field(cuestionario.puntaje_actividad_1)
    p2_list = parse_psfs_json_field(cuestionario.puntaje_actividad_2)
    p3_list = parse_psfs_json_field(cuestionario.puntaje_actividad_3)
    totals = parse_psfs_json_field(cuestionario.puntajeTotal)

    num_sesiones = max(len(p1_list), len(p2_list), len(p3_list), len(totals), 0)
    fecha = (
        cuestionario.fecha_creacion.strftime('%d/%m/%Y')
        if cuestionario.fecha_creacion else ''
    )

    sesiones = []
    for i in range(num_sesiones):
        p1 = p1_list[i] if i < len(p1_list) else 0.0
        p2 = p2_list[i] if i < len(p2_list) else 0.0
        p3 = p3_list[i] if i < len(p3_list) else 0.0
        total = compute_psfs_total(p1, p2, p3)

        sesiones.append({
            'sesion': i + 1,
            'numero': i + 1,
            'actividad_1': _display_score(p1),
            'actividad_2': _display_score(p2),
            'actividad_3': _display_score(p3),
            'puntaje_1': _display_score(p1),
            'puntaje_2': _display_score(p2),
            'puntaje_3': _display_score(p3),
            'total': total,
            'fecha': fecha,
        })

    return sesiones


def scores_from_post(post):
    """Extrae puntajes de un POST (una sesión nueva)."""
    def from_range(name):
        vals = post.getlist(name)
        if not vals:
            single = post.get(name)
            if single is not None and str(single).strip() != '':
                vals = [single]
        return parse_psfs_json_field(vals)

    a1 = from_range('rango1')
    a2 = from_range('rango2')
    a3 = from_range('rango3')

    session = {'actividad_1': a1, 'actividad_2': a2, 'actividad_3': a3, 'total': []}
    return normalize_single_session(session)


def replace_last_psfs_session(cuestionario, nuevos):
    """Reemplaza la última sesión (corregir evaluación actual sin acumular)."""
    session = normalize_single_session(nuevos)
    campos = {
        'puntaje_actividad_1': 'actividad_1',
        'puntaje_actividad_2': 'actividad_2',
        'puntaje_actividad_3': 'actividad_3',
        'puntajeTotal': 'total',
    }
    for campo_db, key in campos.items():
        vals = session.get(key, [])
        if not vals:
            continue
        actuales = parse_psfs_json_field(getattr(cuestionario, campo_db))
        if actuales:
            actuales[-1] = vals[0]
        else:
            actuales = vals
        setattr(cuestionario, campo_db, actuales)


def append_psfs_scores(cuestionario, nuevos):
    """Agrega una nueva sesión de seguimiento."""
    session = normalize_single_session(nuevos)
    campos = {
        'puntaje_actividad_1': 'actividad_1',
        'puntaje_actividad_2': 'actividad_2',
        'puntaje_actividad_3': 'actividad_3',
        'puntajeTotal': 'total',
    }
    for campo_db, key in campos.items():
        vals = session.get(key, [])
        if not vals:
            continue
        actuales = parse_psfs_json_field(getattr(cuestionario, campo_db))
        setattr(cuestionario, campo_db, actuales + vals)


def initial_psfs_scores(nuevos):
    """Puntajes para la primera sesión al crear el cuestionario."""
    session = normalize_single_session(nuevos)
    return {
        'puntaje_actividad_1': session.get('actividad_1', []),
        'puntaje_actividad_2': session.get('actividad_2', []),
        'puntaje_actividad_3': session.get('actividad_3', []),
        'puntajeTotal': session.get('total', []),
    }


def repair_psfs_stored_totals(cuestionario):
    """Recalcula puntajeTotal en BD desde las 3 actividades (corrige datos legacy)."""
    if not cuestionario:
        return

    p1_list = parse_psfs_json_field(cuestionario.puntaje_actividad_1)
    p2_list = parse_psfs_json_field(cuestionario.puntaje_actividad_2)
    p3_list = parse_psfs_json_field(cuestionario.puntaje_actividad_3)
    n = max(len(p1_list), len(p2_list), len(p3_list), 0)
    if n == 0:
        return

    totals = []
    for i in range(n):
        p1 = p1_list[i] if i < len(p1_list) else 0.0
        p2 = p2_list[i] if i < len(p2_list) else 0.0
        p3 = p3_list[i] if i < len(p3_list) else 0.0
        totals.append(compute_psfs_total(p1, p2, p3))

    if totals != parse_psfs_json_field(cuestionario.puntajeTotal):
        cuestionario.puntajeTotal = totals
        cuestionario.save(update_fields=['puntajeTotal'])


def psfs_chart_series(cuestionario):
    """Etiquetas y datos para gráficos de estadísticas por paciente."""
    sesiones = build_psfs_sessions(cuestionario)
    if not sesiones:
        return {'labels': [], 'data': []}
    return {
        'labels': [f'Sesión {s["sesion"]}' for s in sesiones],
        'data': [s['total'] for s in sesiones],
    }
