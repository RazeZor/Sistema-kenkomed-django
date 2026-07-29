"""Variables de sesión multiclinica disponibles en todos los templates."""

from clinicas.branding import url_logo_clinica


def clinica_sesion(request):
  clinica_id = request.session.get('clinica_id')
  clinica_nombre = request.session.get('clinica_nombre', '')
  clinica_logo_url = None
  es_admin_sistema = bool(request.session.get('es_admin', False))
  es_admin_clinica = bool(request.session.get('es_admin_clinica', False))
  tiene_centro = bool(clinica_id)
  es_centro_compartido = False

  if clinica_id:
    from clinicas.models import Clinica, MembresiaClinica

    clinica = Clinica.objects.filter(id=clinica_id, activa=True).first()
    if clinica:
      clinica_nombre = clinica.nombre
      clinica_logo_url = url_logo_clinica(clinica, request)
      if clinica.tipo == 'clinica':
        es_centro_compartido = (
          MembresiaClinica.objects.filter(clinica_id=clinica_id, activo=True).count() > 1
        )

  # Vista global solo cuando es admin KenkoMed sin centro activo en sesión
  estadisticas_globales = es_admin_sistema and not tiene_centro
  puede_ver_estadisticas_centro = tiene_centro and es_admin_clinica
  puede_ver_auditoria = tiene_centro and es_admin_clinica
  puede_ver_agenda_centro = tiene_centro and (es_admin_clinica or es_centro_compartido)

  return {
    'clinica_id': clinica_id,
    'clinica_nombre': clinica_nombre,
    'clinica_logo_url': clinica_logo_url,
    'tiene_logo_clinica': bool(clinica_logo_url),
    'es_admin_sistema': es_admin_sistema,
    'es_admin_clinica': es_admin_clinica,
    'tiene_centro': tiene_centro,
    'es_centro_compartido': es_centro_compartido,
    'estadisticas_globales': estadisticas_globales,
    'estadisticas_centro': puede_ver_estadisticas_centro,
    'puede_ver_estadisticas_centro': puede_ver_estadisticas_centro,
    'puede_ver_agenda_centro': puede_ver_agenda_centro,
    'puede_ver_auditoria': puede_ver_auditoria,
    # Compatibilidad con templates existentes
    'es_admin': es_admin_sistema,
  }
