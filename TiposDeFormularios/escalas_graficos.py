"""Series de datos para gráficos de evolución de escalas clínicas."""
import json

from Login.models import (
    CuestionarioBarthel,
    CuestionarioEQ_5D,
    CuestionarioEvaluacionENA,
    CuestionarioPSFS,
    CuestionarioScrenning,
    Groc,
)


def _serie_vacia():
    return {'labels': [], 'datasets': []}


def _serie_simple(labels, data, label, color, ymin=None, ymax=None):
    if not data:
        return _serie_vacia()
    cfg = {
        'labels': labels,
        'datasets': [{
            'label': label,
            'data': data,
            'borderColor': color,
            'backgroundColor': 'transparent',
            'fill': False,
            'tension': 0.3,
        }],
    }
    if ymin is not None:
        cfg['ymin'] = ymin
    if ymax is not None:
        cfg['ymax'] = ymax
    return cfg


def _psfs(ciclo):
    if not ciclo:
        return _serie_vacia()
    try:
        from TiposDeFormularios.psfs_utils import psfs_chart_series
        raw = psfs_chart_series(CuestionarioPSFS.objects.get(ciclo=ciclo))
        return _serie_simple(raw.get('labels', []), raw.get('data', []), 'PSFS (total)', '#10b981', 0, 10)
    except CuestionarioPSFS.DoesNotExist:
        return _serie_vacia()


def _groc(ciclo):
    if not ciclo:
        return _serie_vacia()
    try:
        groc = Groc.objects.get(ciclo=ciclo)
        raw = groc.puntajeGroc
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, list):
            return _serie_vacia()
        values = []
        for item in raw:
            if isinstance(item, dict):
                values.append(int(item.get('puntaje', 0)))
            else:
                values.append(int(item))
        labels = [f'S{i + 1}' for i in range(len(values))]
        return _serie_simple(labels, values, 'GROC', '#0ea5e9', -7, 7)
    except (Groc.DoesNotExist, TypeError, ValueError):
        return _serie_vacia()


def _ena(ciclo):
    if not ciclo:
        return _serie_vacia()
    try:
        ena = CuestionarioEvaluacionENA.objects.get(ciclo=ciclo)
        raw = ena.estado_por_sesion or []
        if isinstance(raw, str):
            raw = json.loads(raw)
        if not isinstance(raw, list):
            return _serie_vacia()
        values = [int(item.get('level', 0)) if isinstance(item, dict) else int(item) for item in raw]
        labels = [f'S{i + 1}' for i in range(len(values))]
        return _serie_simple(labels, values, 'ENA (dolor 0–10)', '#ef4444', 0, 10)
    except (CuestionarioEvaluacionENA.DoesNotExist, TypeError, ValueError):
        return _serie_vacia()


def _eq5d(ciclo):
    if not ciclo:
        return _serie_vacia()
    try:
        eq = CuestionarioEQ_5D.objects.get(ciclo=ciclo)
        vas = eq.vas_score or []
        if not vas:
            return _serie_vacia()
        labels = [f'S{i + 1}' for i in range(len(vas))]
        return _serie_simple(labels, list(vas), 'EQ-5D EVA', '#8b5cf6', 0, 100)
    except CuestionarioEQ_5D.DoesNotExist:
        return _serie_vacia()


def _barthel(ciclo):
    if not ciclo:
        return _serie_vacia()
    try:
        b = CuestionarioBarthel.objects.get(ciclo=ciclo)
        totals = json.loads(b.puntaje_total or '[]')
        if not totals:
            return _serie_vacia()
        labels = [f'S{i + 1}' for i in range(len(totals))]
        return _serie_simple(labels, totals, 'Barthel (total)', '#f59e0b', 0, 100)
    except (CuestionarioBarthel.DoesNotExist, TypeError, ValueError):
        return _serie_vacia()


def _screening(ciclo):
    if not ciclo:
        return _serie_vacia()
    try:
        s = CuestionarioScrenning.objects.get(ciclo=ciclo)
        puntajes = s.Puntaje_Sesion
        if isinstance(puntajes, list):
            values = puntajes
        else:
            values = [puntajes] if puntajes is not None else []
        if not values:
            return _serie_vacia()
        labels = [f'S{i + 1}' for i in range(len(values))]
        return _serie_simple(labels, values, 'Screening Örebro', '#6366f1', 0, 12)
    except CuestionarioScrenning.DoesNotExist:
        return _serie_vacia()


def _lefs(ciclo):
    from TiposDeFormularios.models import EvaluacionLEFS
    if not ciclo:
        return _serie_vacia()
    qs = EvaluacionLEFS.objects.filter(ciclo=ciclo).order_by('fecha_evaluacion')
    if not qs.exists():
        return _serie_vacia()
    labels = [e.fecha_evaluacion.strftime('%d/%m/%y') for e in qs]
    data = [e.get_total_puntos() for e in qs]
    return _serie_simple(labels, data, 'LEFS (puntos)', '#059669', 0, 80)


def _oswestry(ciclo):
    from TiposDeFormularios.models import EvaluacionOswestry
    if not ciclo:
        return _serie_vacia()
    qs = EvaluacionOswestry.objects.filter(ciclo=ciclo).order_by('fecha_evaluacion')
    if not qs.exists():
        return _serie_vacia()
    labels = [e.fecha_evaluacion.strftime('%d/%m/%y') for e in qs]
    data = [e.get_porcentaje_incapacidad() for e in qs]
    return _serie_simple(labels, data, 'Oswestry ODI (%)', '#1e40af', 0, 100)


def _quickdash(ciclo):
    from TiposDeFormularios.models import EvaluacionQuickDASH
    if not ciclo:
        return _serie_vacia()
    qs = EvaluacionQuickDASH.objects.filter(ciclo=ciclo).order_by('fecha_evaluacion')
    if not qs.exists():
        return _serie_vacia()
    labels = [e.fecha_evaluacion.strftime('%d/%m/%y') for e in qs]
    data = [e.get_porcentaje_discapacidad() for e in qs]
    return _serie_simple(labels, data, 'QuickDASH (% discapacidad)', '#7c3aed', 0, 100)


def _womac(ciclo):
    from TiposDeFormularios.models import EvaluacionWOMAC
    if not ciclo:
        return _serie_vacia()
    qs = EvaluacionWOMAC.objects.filter(ciclo=ciclo).order_by('fecha_evaluacion')
    if not qs.exists():
        return _serie_vacia()
    labels = [e.fecha_evaluacion.strftime('%d/%m/%y') for e in qs]
    return {
        'labels': labels,
        'datasets': [
            {'label': 'Total', 'data': [e.get_total_puntos() for e in qs], 'borderColor': '#d97706', 'backgroundColor': 'rgba(217,119,6,0.1)', 'fill': False, 'tension': 0.3},
            {'label': 'Dolor', 'data': [e.get_puntaje_dolor() for e in qs], 'borderColor': '#ef4444', 'backgroundColor': 'rgba(239,68,68,0.08)', 'fill': False, 'tension': 0.3},
            {'label': 'Rigidez', 'data': [e.get_puntaje_rigidez() for e in qs], 'borderColor': '#f59e0b', 'backgroundColor': 'rgba(245,158,11,0.08)', 'fill': False, 'tension': 0.3},
            {'label': 'Función', 'data': [e.get_puntaje_funcion() for e in qs], 'borderColor': '#10b981', 'backgroundColor': 'rgba(16,185,129,0.08)', 'fill': False, 'tension': 0.3},
        ],
        'ymin': 0,
        'ymax': 96,
    }


_BUILDERS = {
    'psfs': _psfs,
    'groc': _groc,
    'eq5d': _eq5d,
    'barthel': _barthel,
    'ena': _ena,
    'screening': _screening,
    'oswestry': _oswestry,
    'lefs': _lefs,
    'quickdash': _quickdash,
    'womac': _womac,
}


def obtener_graficos_ciclo(ciclo):
    """Dict tipo_escala → configuración de gráfico para un ciclo."""
    return {codigo: builder(ciclo) for codigo, builder in _BUILDERS.items()}


def obtener_graficos_paciente(paciente):
    """Compatibilidad: usa ciclo activo del paciente si existe."""
    from ciclos_clinicos.selectors import obtener_ciclo_activo
    ciclo = obtener_ciclo_activo(paciente, paciente.clinica_id) if paciente else None
    return obtener_graficos_ciclo(ciclo)


def graficos_para_registros_sesion(ciclo, registros_escalas):
    """Gráficos únicos para las escalas aplicadas en una sesión."""
    todos = obtener_graficos_ciclo(ciclo)
    vistos = set()
    bloques = []
    for reg in registros_escalas:
        codigo = reg.tipo_escala
        if codigo in vistos:
            continue
        cfg = todos.get(codigo, _serie_vacia())
        if not cfg.get('labels'):
            continue
        vistos.add(codigo)
        bloques.append({
            'codigo': codigo,
            'nombre': reg.get_tipo_escala_display(),
            'canvas_id': f'chart_escala_{codigo}',
            'config': cfg,
        })
    return bloques


def serie_json_para_vista(ciclo, codigo):
    """Lista de puntos {fecha, valor, ...} para plantillas de cuestionario."""
    cfg = _BUILDERS.get(codigo, lambda c: _serie_vacia())(ciclo)
    if not cfg.get('labels'):
        return []
    ds = cfg['datasets'][0] if cfg.get('datasets') else {}
    data = ds.get('data', [])
    out = []
    for i, label in enumerate(cfg['labels']):
        point = {'fecha': label, 'valor': data[i] if i < len(data) else None}
        if codigo == 'lefs':
            point['puntos'] = point['valor']
            point['porcentaje'] = round((point['valor'] or 0) / 80 * 100, 1)
        elif codigo == 'oswestry':
            point['porcentaje'] = point['valor']
        elif codigo == 'quickdash':
            point['porcentaje'] = point['valor']
        elif codigo == 'womac':
            point['total'] = data[i] if i < len(data) else None
        out.append(point)
    if codigo == 'womac' and cfg.get('datasets'):
        for i, label in enumerate(cfg['labels']):
            if i < len(out):
                out[i]['dolor'] = cfg['datasets'][1]['data'][i]
                out[i]['rigidez'] = cfg['datasets'][2]['data'][i]
                out[i]['funcion'] = cfg['datasets'][3]['data'][i]
                out[i]['total'] = cfg['datasets'][0]['data'][i]
    return out
