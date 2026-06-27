"""Países del mundo (ISO 3166-1 alpha-2) con nombres en español.

Fuente: CLDR vía Babel, generado en Login/data/paises_es.json.
No se usa API en tiempo de ejecución: el listado es estático para rendimiento y disponibilidad offline.
"""
import json
from functools import lru_cache
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parent / 'data' / 'paises_es.json'

# Código legacy usado antes de ampliar el listado
PAIS_OTRO_LEGACY = 'OT'


@lru_cache(maxsize=1)
def _cargar_paises_raw():
    with _DATA_FILE.open(encoding='utf-8') as f:
        return json.load(f)


def paises_iso_es():
    """Lista de tuplas (codigo_iso, nombre_es)."""
    return [(code, name) for code, name in _cargar_paises_raw()]


def paises_documento_para_select():
    """Opciones para <select>: placeholder + todos los países."""
    return [('', '— Seleccione país —'), *paises_iso_es()]


@lru_cache(maxsize=1)
def mapa_nombres_paises():
    """Dict código ISO → nombre en español (+ legacy OT)."""
    mapping = dict(paises_iso_es())
    mapping[PAIS_OTRO_LEGACY] = 'Otro país'
    return mapping


def nombre_pais(codigo):
    if not codigo:
        return ''
    return mapa_nombres_paises().get(str(codigo).upper(), codigo)
