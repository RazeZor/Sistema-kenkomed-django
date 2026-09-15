"""Context processor para poner las características del plan activo a disposición de los templates HTML."""

def plan_features(request):
    clinica_id = request.session.get('clinica_id')
    es_admin_sistema = bool(request.session.get('es_admin', False))

    # Por defecto (sin clínica activa), si es Admin KenkoMed tiene acceso total
    if not clinica_id:
        return {
            'features': {
                'qr_anamnesis': es_admin_sistema,
                'recetas_digitales': es_admin_sistema,
                'reportes_dss': es_admin_sistema,
                'exportacion_arco': es_admin_sistema,
                'auditoria_pdf': es_admin_sistema,
                'multi_seda': es_admin_sistema,
                'roles_avanzados': es_admin_sistema,
                'logo_personalizado': es_admin_sistema,
                'dashboard_gerencial': es_admin_sistema,
            },
            'es_plan_legacy': es_admin_sistema,
            'nombre_plan': 'Administración KenkoMed' if es_admin_sistema else 'Sin Plan',
        }

    from clinicas.models import Clinica
    from planes.models import SuscripcionClinica

    clinica = Clinica.objects.filter(id=clinica_id, activa=True).first()
    suscripcion = None
    if clinica:
        suscripcion = getattr(clinica, 'suscripcion', None)

    if not suscripcion:
        # Fallback de seguridad: si existe la clínica pero aún no tiene objeto SuscripcionClinica
        return {
            'features': {
                'qr_anamnesis': True,
                'recetas_digitales': True,
                'reportes_dss': True,
                'exportacion_arco': True,
                'auditoria_pdf': True,
                'multi_seda': True,
                'roles_avanzados': True,
                'logo_personalizado': True,
                'dashboard_gerencial': True,
            },
            'es_plan_legacy': True,
            'nombre_plan': 'Legacy Full Access',
        }

    return {
        'features': {
            'qr_anamnesis': suscripcion.tiene_feature('permite_qr_anamnesis'),
            'recetas_digitales': suscripcion.tiene_feature('permite_recetas_digitales'),
            'reportes_dss': suscripcion.tiene_feature('permite_reportes_dss'),
            'exportacion_arco': suscripcion.tiene_feature('permite_exportacion_arco'),
            'auditoria_pdf': suscripcion.tiene_feature('permite_auditoria_pdf'),
            'multi_seda': suscripcion.tiene_feature('permite_multi_seda'),
            'roles_avanzados': suscripcion.tiene_feature('permite_roles_avanzados'),
            'logo_personalizado': suscripcion.tiene_feature('permite_logo_personalizado'),
            'dashboard_gerencial': suscripcion.tiene_feature('permite_dashboard_gerencial'),
        },
        'es_plan_legacy': suscripcion.es_legacy,
        'nombre_plan': suscripcion.plan.nombre if suscripcion.plan else 'Sin Plan',
    }
