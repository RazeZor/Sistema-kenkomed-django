import mimetypes
from pathlib import Path

from django.conf import settings

LOGO_CID = 'logo_correo'


def _ruta_logo_kenkomed():
    candidatos = [
        Path(settings.BASE_DIR) / 'Login' / 'static' / 'image' / 'LogoKenkoMed.png',
        Path(settings.BASE_DIR) / 'static' / 'images' / 'logo.png',
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return None


def resolver_branding_correo(clinica=None):
    """
    Devuelve datos de marca para correos: logo embebido (CID) y nombre visible.
    Prioriza logo de la clínica; si no hay, usa KenkoMed.
    """
    nombre_marca = 'KenkoMed'
    es_marca_clinica = False
    ruta_logo = _ruta_logo_kenkomed()
    nombre_archivo = 'LogoKenkoMed.png'

    if clinica and clinica.logo:
        try:
            if clinica.logo.storage.exists(clinica.logo.name):
                ruta_logo = Path(clinica.logo.path)
                nombre_marca = clinica.nombre
                es_marca_clinica = True
                nombre_archivo = Path(clinica.logo.name).name
        except (ValueError, OSError):
            pass

    return {
        'nombre_marca': nombre_marca,
        'es_marca_clinica': es_marca_clinica,
        'tiene_logo': ruta_logo is not None and ruta_logo.exists(),
        'logo_cid': LOGO_CID,
        'logo_ruta': ruta_logo,
        'logo_filename': nombre_archivo,
    }


def tipo_mime_logo(ruta):
    if not ruta:
        return 'image/png'
    mime, _ = mimetypes.guess_type(str(ruta))
    return mime or 'image/png'


def url_logo_clinica(clinica, request=None):
    """URL del logo de la clínica para plantillas web/PDF, o None."""
    if not clinica or not clinica.logo:
        return None
    try:
        if not clinica.logo.storage.exists(clinica.logo.name):
            return None
        url = clinica.logo.url
        if request:
            return request.build_absolute_uri(url)
        return url
    except (ValueError, OSError):
        return None
