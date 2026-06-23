def obtener_clinica_id(request):
    return request.session.get('clinica_id')


def es_admin_sistema(request):
    """Admin KenkoMed (EsAdmin): acceso global solo sin centro activo en sesión."""
    return request.session.get('es_admin', False)


def es_admin_de_clinica(request):
    """Administrador del centro activo en sesión (rol admin en MembresiaClinica)."""
    return bool(request.session.get('es_admin_clinica'))


def tiene_centro_en_sesion(request):
    return bool(obtener_clinica_id(request))


def filtrar_por_clinica_sesion(request, queryset, lookup='clinica_id'):
    """
    Restringe un queryset a la clínica de la sesión.
    Si hay clinica_id en sesión, SIEMPRE filtra (incluso admin KenkoMed).
    Sin clinica_id: admin KenkoMed ve todo; el resto no ve nada.
    """
    clinica_id = obtener_clinica_id(request)
    if clinica_id:
        return queryset.filter(**{lookup: clinica_id})
    if es_admin_sistema(request):
        return queryset
    return queryset.none()


def paciente_pertenece_a_sesion(request, paciente):
    if not paciente:
        return False
    clinica_id = obtener_clinica_id(request)
    if clinica_id:
        return paciente.clinica_id == clinica_id
    if es_admin_sistema(request):
        return True
    return False


def filtrar_pacientes_por_sesion(request, queryset=None):
    from Login.models import Paciente

    if queryset is None:
        queryset = Paciente.objects.all()
    return filtrar_por_clinica_sesion(request, queryset, lookup='clinica_id')


def filtrar_tokens_formulario_por_sesion(request, queryset=None):
    from FormularioInicial.models import TokenFormulario

    if queryset is None:
        queryset = TokenFormulario.objects.all()
    return filtrar_por_clinica_sesion(request, queryset, lookup='paciente__clinica_id')


def filtrar_auditoria_por_sesion(request, queryset=None):
    from Login.models import AuditoriaAcceso

    if queryset is None:
        queryset = AuditoriaAcceso.objects.all()
    return filtrar_por_clinica_sesion(request, queryset, lookup='clinica_id')


def filtrar_reservas_por_sesion(request, queryset=None):
    from Login.models import Reserva
    from clinicas.models import MembresiaClinica

    if queryset is None:
        queryset = Reserva.objects.all()

    clinica_id = obtener_clinica_id(request)
    if clinica_id:
        clinico_ids = list(
            MembresiaClinica.objects.filter(clinica_id=clinica_id, activo=True)
            .values_list('clinico_id', flat=True)
        )
        if not clinico_ids:
            return queryset.none()
        return queryset.filter(clinico_id__in=clinico_ids)

    if es_admin_sistema(request):
        return queryset
    return queryset.none()


def obtener_paciente_por_rut(request, rut):
    from Login.models import Paciente

    if not rut:
        return None
    try:
        paciente = Paciente.objects.get(rut=rut)
    except Paciente.DoesNotExist:
        return None

    if paciente_pertenece_a_sesion(request, paciente):
        return paciente
    return None


def obtener_clinicos_de_sesion(request):
    from clinicas.models import MembresiaClinica

    clinica_id = obtener_clinica_id(request)
    if clinica_id:
        return list(
            MembresiaClinica.objects.filter(clinica_id=clinica_id, activo=True)
            .values_list('clinico_id', flat=True)
        )

    if es_admin_sistema(request):
        from Login.models import Clinico
        return list(Clinico.objects.values_list('rut', flat=True))

    return []


def obtener_clinicos_del_centro(request):
    from Login.models import Clinico

    ids = obtener_clinicos_de_sesion(request)
    if not ids:
        return Clinico.objects.none()
    return Clinico.objects.filter(rut__in=ids).order_by('nombre', 'apellido')


def clinico_pertenece_a_sesion(request, clinico):
    from clinicas.models import MembresiaClinica

    if not clinico:
        return False

    clinica_id = obtener_clinica_id(request)
    if clinica_id:
        return MembresiaClinica.objects.filter(
            clinico=clinico,
            clinica_id=clinica_id,
            activo=True,
        ).exists()

    if es_admin_sistema(request):
        return True
    return False


def obtener_clinica_de_sesion(request):
    from clinicas.models import Clinica

    clinica_id = obtener_clinica_id(request)
    if not clinica_id:
        return None
    return Clinica.objects.filter(id=clinica_id, activa=True).first()


def obtener_membresias_del_centro(request):
    from clinicas.models import MembresiaClinica

    clinica_id = obtener_clinica_id(request)
    if not clinica_id:
        return MembresiaClinica.objects.none()
    return (
        MembresiaClinica.objects.filter(clinica_id=clinica_id, activo=True)
        .select_related('clinico')
        .order_by('clinico__nombre', 'clinico__apellido')
    )


def requiere_centro_o_admin_sistema(request):
    """True si el usuario puede operar en la app con datos clínicos."""
    return tiene_centro_en_sesion(request) or es_admin_sistema(request)
