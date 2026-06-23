def obtener_clinica_id(request):
    return request.session.get('clinica_id')


def es_admin_sistema(request):
    return request.session.get('es_admin', False)


def paciente_pertenece_a_sesion(request, paciente):
    if es_admin_sistema(request):
        return True
    clinica_id = obtener_clinica_id(request)
    if not clinica_id:
        return False
    return paciente.clinica_id == clinica_id


def filtrar_pacientes_por_sesion(request, queryset=None):
    from Login.models import Paciente

    if queryset is None:
        queryset = Paciente.objects.all()

    if es_admin_sistema(request):
        return queryset

    clinica_id = obtener_clinica_id(request)
    if not clinica_id:
        return Paciente.objects.none()

    return queryset.filter(clinica_id=clinica_id)


def obtener_paciente_por_rut(request, rut):
    from Login.models import Paciente

    try:
        paciente = Paciente.objects.get(rut=rut)
    except Paciente.DoesNotExist:
        return None

    if paciente_pertenece_a_sesion(request, paciente):
        return paciente
    return None


def obtener_clinicos_de_sesion(request):
    from clinicas.models import MembresiaClinica

    if es_admin_sistema(request):
        from Login.models import Clinico
        return list(Clinico.objects.values_list('rut', flat=True))

    clinica_id = obtener_clinica_id(request)
    if not clinica_id:
        return []

    return list(
        MembresiaClinica.objects.filter(clinica_id=clinica_id, activo=True)
        .values_list('clinico_id', flat=True)
    )


def obtener_clinicos_del_centro(request):
    from Login.models import Clinico

    ids = obtener_clinicos_de_sesion(request)
    if not ids:
        return Clinico.objects.none()
    return Clinico.objects.filter(rut__in=ids).order_by('nombre', 'apellido')


def clinico_pertenece_a_sesion(request, clinico):
    from clinicas.models import MembresiaClinica

    if es_admin_sistema(request):
        return True
    clinica_id = obtener_clinica_id(request)
    if not clinica_id or not clinico:
        return False
    return MembresiaClinica.objects.filter(
        clinico=clinico,
        clinica_id=clinica_id,
        activo=True,
    ).exists()


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
