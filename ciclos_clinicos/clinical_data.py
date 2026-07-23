"""Acceso a datos clínicos scoped por ciclo."""

from Login.models import formularioClinico


def formulario_del_ciclo(ciclo):
    if not ciclo:
        return None
    try:
        return ciclo.formulario
    except formularioClinico.DoesNotExist:
        return None


def tiene_anamnesis_ciclo(ciclo):
    return formulario_del_ciclo(ciclo) is not None


def obtener_o_crear_formulario(ciclo, paciente, clinico):
    form = formulario_del_ciclo(ciclo)
    if form:
        return form, False
    form = formularioClinico(ciclo=ciclo, paciente=paciente, clinico=clinico)
    form.save()
    return form, True


def get_cuestionario_por_ciclo(modelo, ciclo, default=None):
    if not ciclo:
        return default
    try:
        return modelo.objects.get(ciclo=ciclo)
    except modelo.DoesNotExist:
        return default


def get_or_create_cuestionario_por_ciclo(modelo, ciclo, paciente, **defaults):
    return modelo.objects.get_or_create(ciclo=ciclo, defaults={'paciente': paciente, **defaults})
