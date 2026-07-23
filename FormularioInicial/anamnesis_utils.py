"""Utilidades para guardar y precargar la anamnesis (formularioClinico)."""
import json


def _parse_stored_list(value):
    """Convierte un campo JSON/lista/str del modelo a lista Python."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except (json.JSONDecodeError, TypeError):
            return [value]
    return [value]


def _primer_radio_json(value):
    items = _parse_stored_list(value)
    return items[0] if items else None


def valores_anamnesis_desde_post(request):
    """Extrae todos los campos de anamnesis desde POST (misma forma que el guardado histórico)."""
    return {
        'medicamentos': request.POST.getlist('medicamentos'),
        'duracionDolor': request.POST.get('btnradio1'),
        'caracteristicasDeDolor': json.dumps(request.POST.getlist('caracteristicas')),
        'ubicacionDolor': json.dumps(request.POST.getlist('ubicacionDolor')),
        'dolorIntensidad': json.dumps(request.POST.getlist('intensidad')),
        'causaDolor': request.POST.get('causaDolor'),
        'accidenteLaboral': json.dumps(request.POST.getlist('accidenteLaboral')),
        'calidadAtencion': request.POST.get('calidadAtencion'),
        'opinionProblemaEnfermeda': request.POST.get('diagnosis'),
        'opinionCuraDolor': request.POST.get('cure'),
        'TiposDeEnfermedades': json.dumps(request.POST.getlist('TiposDeEnfermedades')),
        'actividades_afectadas': json.dumps(request.POST.getlist('actividades_afectadas')),
        'parametros': json.dumps(request.POST.getlist('parametros')),
        'pregunta1_nivelDeSalud': request.POST.get('pregunta1_nivelDeSalud'),
        'pregunta3_frecuencia_De_Suenio': request.POST.get('op3'),
        'pregunta4_opinion_peso_actual': request.POST.get('pregunta4_opinion_peso_actual'),
        'pregunta5_ConsumoComidaRapida': request.POST.get('op5'),
        'hora_acostarse': request.POST.get('hora_acostarse'),
        'tiempo_dormirse': request.POST.get('tiempo_dormirse'),
        'hora_despertar': request.POST.get('hora_despertar'),
        'hora_levantarse': request.POST.get('hora_levantarse'),
        'despertares': request.POST.get('despertares'),
        'pregunta6_PorcionesDeFrutas': request.POST.get('op6'),
        'pregunta7_ejercicioDias': request.POST.get('op7'),
        'pregunta8_minutosPorEjercicios': request.POST.get('op8'),
        'proposito': request.POST.get('proposito'),
        'red_de_apoyo': request.POST.get('red_de_apoyo'),
        'placer_cosas': request.POST.get('placer_cosas'),
        'deprimido': request.POST.get('deprimido'),
        'ansioso': request.POST.get('ansioso'),
        'preocupacion': request.POST.get('preocupacion'),
        'NicotinaSiOno': request.POST.get('NicotinaSiOno'),
        'condicionNicotina': request.POST.get('frecuenciaNicotina'),
        'nicotinaPreocupacion': request.POST.get('preocupacionNicotina'),
        'AlcoholSiOno': request.POST.get('AlcoholSiOno'),
        'condicionAlcohol': request.POST.get('frecuenciaAlcohol'),
        'AlcoholPreocupacion': request.POST.get('preocupacionAlcohol'),
        'drogasSiOno': request.POST.get('drogasSiOno'),
        'condicionDrogas': request.POST.get('CantidadDrogras'),
        'DrogasPreocupacion': request.POST.get('DrogasPreocupacion'),
        'marihuanaSiOno': request.POST.get('marihuanaSiOno'),
        'condicionMarihuana': request.POST.get('frecuenciaMarihuana'),
        'marihuanaPreocupacion': request.POST.get('marihuanaPreocupacion'),
        'preguntas2': json.dumps(request.POST.getlist('preguntas2')),
        'AreasMotivacion': json.dumps(request.POST.getlist('motivacion')),
        'motivacion_Salud': request.POST.get('motivacion_Salud'),
    }


def aplicar_valores_a_formulario(form, valores, clinico=None):
    for campo, valor in valores.items():
        setattr(form, campo, valor)
    if clinico is not None:
        form.clinico = clinico
    form.save()
    return form


def guardar_anamnesis_desde_post(request, paciente, clinico, ciclo=None):
    """Crea o actualiza la anamnesis del ciclo. Retorna (formulario, es_edicion)."""
    from Login.models import formularioClinico
    from ciclos_clinicos.clinical_data import formulario_del_ciclo
    from ciclos_clinicos.services import asegurar_ciclo_editable, obtener_ciclo_desde_request

    if ciclo is None:
        ciclo = obtener_ciclo_desde_request(
            request, paciente, crear_si_ausente=True, clinico=clinico,
        )
    if not ciclo:
        raise ValueError('No hay ciclo clínico activo para guardar la anamnesis.')
    asegurar_ciclo_editable(ciclo)

    valores = valores_anamnesis_desde_post(request)
    form = formulario_del_ciclo(ciclo)
    if form:
        aplicar_valores_a_formulario(form, valores, clinico=clinico)
        if not form.paciente_id:
            form.paciente = paciente
            form.save(update_fields=['paciente'])
        return form, True
    form = formularioClinico(paciente=paciente, ciclo=ciclo, clinico=clinico, **valores)
    form.save()
    return form, False


def _scalar_json_field(value):
    """Normaliza campos JSON que a veces guardan un string simple."""
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return str(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, str):
                return parsed
        except (json.JSONDecodeError, TypeError):
            pass
        return stripped
    return str(value)


def prefill_desde_formulario(form):
    """Dict para precargar el formulario HTML vía JavaScript."""
    ubicaciones = _parse_stored_list(form.ubicacionDolor)
    intensidades = _parse_stored_list(form.dolorIntensidad)
    mapa_dolor = [
        {'zona': ubicaciones[i], 'intensidad': intensidades[i] if i < len(intensidades) else ''}
        for i in range(len(ubicaciones))
    ]

    def _str_field(val):
        if val is None:
            return ''
        if isinstance(val, (list, dict)):
            return json.dumps(val, ensure_ascii=False)
        return str(val)

    radios = {
        'btnradio1': form.duracionDolor,
        'accidenteLaboral': _primer_radio_json(form.accidenteLaboral),
        'calidadAtencion': form.calidadAtencion,
        'diagnosis': form.opinionProblemaEnfermeda,
        'cure': form.opinionCuraDolor,
        'op3': form.pregunta3_frecuencia_De_Suenio,
        'op5': form.pregunta5_ConsumoComidaRapida,
        'op6': form.pregunta6_PorcionesDeFrutas,
        'op7': form.pregunta7_ejercicioDias,
        'op8': form.pregunta8_minutosPorEjercicios,
        'proposito': form.proposito,
        'red_de_apoyo': form.red_de_apoyo,
        'placer_cosas': form.placer_cosas,
        'deprimido': form.deprimido,
        'ansioso': form.ansioso,
        'preocupacion': form.preocupacion,
        'NicotinaSiOno': _scalar_json_field(form.NicotinaSiOno),
        'AlcoholSiOno': _scalar_json_field(form.AlcoholSiOno),
        'drogasSiOno': _scalar_json_field(form.drogasSiOno),
        'marihuanaSiOno': _scalar_json_field(form.marihuanaSiOno),
        'genero': None,
        'cobertura': None,
        'trabajo': None,
    }

    text = {
        'causaDolor': form.causaDolor or '',
        'pregunta1_nivelDeSalud': form.pregunta1_nivelDeSalud or '',
        'pregunta4_opinion_peso_actual': form.pregunta4_opinion_peso_actual or '',
        'hora_acostarse': form.hora_acostarse or '',
        'tiempo_dormirse': form.tiempo_dormirse or '',
        'hora_despertar': form.hora_despertar or '',
        'hora_levantarse': form.hora_levantarse or '',
        'despertares': form.despertares or '',
        'frecuenciaNicotina': form.condicionNicotina or '',
        'preocupacionNicotina': form.nicotinaPreocupacion or '',
        'frecuenciaAlcohol': form.condicionAlcohol or '',
        'preocupacionAlcohol': form.AlcoholPreocupacion or '',
        'CantidadDrogras': form.condicionDrogas or '',
        'DrogasPreocupacion': form.DrogasPreocupacion or '',
        'frecuenciaMarihuana': form.condicionMarihuana or '',
        'marihuanaPreocupacion': form.marihuanaPreocupacion or '',
        'motivacion_Salud': form.motivacion_Salud or '',
    }

    checks = {
        'caracteristicas': _parse_stored_list(form.caracteristicasDeDolor),
        'medicamentos': _parse_stored_list(form.medicamentos),
        'TiposDeEnfermedades': _parse_stored_list(form.TiposDeEnfermedades),
        'actividades_afectadas': _parse_stored_list(form.actividades_afectadas),
        'preguntas2': _parse_stored_list(form.preguntas2),
        'motivacion': _parse_stored_list(form.AreasMotivacion),
    }

    return {
        'radios': {k: v for k, v in radios.items() if v},
        'text': text,
        'selects': {'causaDolor': form.causaDolor or ''},
        'checks': checks,
        'mapa_dolor': mapa_dolor,
        'actividades_afectadas': _parse_stored_list(form.actividades_afectadas),
        'parametros': _parse_stored_list(form.parametros),
    }
