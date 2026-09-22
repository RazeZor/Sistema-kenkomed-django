"""Context processor para inyectar el resumen de deuda y pack activo en los templates."""


def resumen_pagos_paciente(request):
    """
    Inyecta en el contexto global el estado financiero del paciente activo en sesión.
    Solo actúa si hay un 'rut_paciente_activo' en la sesión (puesto por las vistas de ficha/historial).
    """
    rut_paciente = request.session.get('rut_paciente_activo')
    clinica_id = request.session.get('clinica_id')

    if not rut_paciente or not clinica_id:
        return {
            'pago_deuda_paciente': None,
            'pago_pack_activo': None,
        }

    try:
        from .models import DeudaPaciente, PackAtencion
        deuda = DeudaPaciente.objects.filter(
            paciente_id=rut_paciente,
            clinica_id=clinica_id,
        ).first()

        pack_activo = PackAtencion.objects.filter(
            paciente_id=rut_paciente,
            clinica_id=clinica_id,
            estado=PackAtencion.ESTADO_ACTIVO,
        ).order_by('-fecha_compra').first()
    except Exception:
        deuda = None
        pack_activo = None

    return {
        'pago_deuda_paciente': deuda,
        'pago_pack_activo': pack_activo,
    }
