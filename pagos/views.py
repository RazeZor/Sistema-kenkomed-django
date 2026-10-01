from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from decimal import Decimal

from Login.models import Paciente, Clinico
from clinicas.models import Clinica
from clinicas.utils import obtener_paciente_por_rut
from Login.auditoria import registrar_auditoria
from ProyectoMainAPP.decorators.login_requerido import (
    requiere_clinico,
    requiere_admin_clinica,
)
from .models import PackAtencion, RegistroPago, DeudaPaciente
from . import services


# ────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────

def _clinica_activa(request):
    """Retorna la Clinica activa de la sesión o None."""
    clinica_id = request.session.get('clinica_id')
    if not clinica_id:
        return None
    return Clinica.objects.filter(id=clinica_id, activa=True).first()


def _clinico_activo(request):
    rut = request.session.get('rut_clinico')
    if not rut:
        return None
    return Clinico.objects.filter(rut=rut).first()


def _puede_gestionar_pagos(request):
    """Secretaria, admin_clinica o admin sistema pueden gestionar pagos."""
    return (
        request.session.get('es_admin')
        or request.session.get('es_admin_clinica')
        or request.session.get('es_secretaria')
    )


# ────────────────────────────────────────────
# Dashboard principal de pagos
# ────────────────────────────────────────────

@requiere_clinico
def dashboard_pagos(request):
    clinica = _clinica_activa(request)
    if not clinica:
        messages.error(request, 'No tienes una clínica activa.')
        return redirect('panel')

    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para acceder al módulo de pagos.')
        return redirect('panel')

    # Servicios verifican packs vencidos
    services.verificar_vencimiento_packs(clinica)

    resumen = services.obtener_resumen_financiero_clinica(clinica)

    # Pacientes con deuda para la tabla principal (sesiones sin pago O monto pendiente de pack)
    from django.db.models import Q
    deudas_qs = (
        DeudaPaciente.objects.filter(clinica=clinica)
        .filter(Q(sesiones_sin_pago__gt=0) | Q(monto_pendiente__gt=0))
        .select_related('paciente')
        .order_by('-monto_pendiente', '-sesiones_sin_pago')
    )
    deudas = Paginator(deudas_qs, 5).get_page(request.GET.get('page_deudas', 1))

    # Packs activos (paginado de 5 en 5)
    packs_activos_qs = (
        PackAtencion.objects.filter(clinica=clinica, estado=PackAtencion.ESTADO_ACTIVO)
        .select_related('paciente')
        .order_by('-fecha_compra')
    )
    packs_activos = Paginator(packs_activos_qs, 5).get_page(request.GET.get('page_packs', 1))

    # Pagos recientes del centro (paginado de 5 en 5)
    pagos_recientes_qs = (
        RegistroPago.objects.filter(clinica=clinica)
        .exclude(estado=RegistroPago.ESTADO_ANULADO)
        .select_related('paciente', 'registrado_por', 'sesion_kinesica', 'pack')
        .order_by('-fecha_registro')
    )
    pagos_recientes = Paginator(pagos_recientes_qs, 5).get_page(request.GET.get('page_pagos', 1))

    registrar_auditoria(request, 'consulta_pagos', detalle='Dashboard de pagos del centro')

    ctx = {
        'clinica': clinica,
        'resumen': resumen,
        'deudas': deudas,
        'pagos_recientes': pagos_recientes,
        'packs_activos': packs_activos,
        'hoy': timezone.localdate(),
        'medios_pago': RegistroPago.MEDIOS_PAGO,
        'estados_pago': RegistroPago.ESTADOS,
    }
    return render(request, 'pagos/dashboard_pagos.html', ctx)


# ────────────────────────────────────────────
# Detalle de pagos por paciente
# ────────────────────────────────────────────

@requiere_clinico
def detalle_pagos_paciente(request):
    rut = request.GET.get('rut') or request.POST.get('rut')
    if not rut:
        messages.error(request, 'Debes indicar el RUT del paciente.')
        return redirect('pagos:dashboard')

    clinica = _clinica_activa(request)
    if not clinica:
        messages.error(request, 'No tienes una clínica activa.')
        return redirect('panel')

    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('pagos:dashboard')

    services.verificar_vencimiento_packs(clinica)
    services.recalcular_deuda(paciente, clinica)
    resumen = services.obtener_resumen_financiero_paciente(paciente, clinica)
    config = services.obtener_configuracion(clinica)

    # Paginación de 5 en 5 para historial de packs
    packs_historico_qs = PackAtencion.objects.filter(
        paciente=paciente, clinica=clinica
    ).order_by('-fecha_compra')
    packs_historico = Paginator(packs_historico_qs, 5).get_page(request.GET.get('page_packs', 1))

    # Paginación de 5 en 5 para historial de pagos
    pagos_recientes_qs = (
        RegistroPago.objects.filter(paciente=paciente, clinica=clinica)
        .exclude(estado=RegistroPago.ESTADO_ANULADO)
        .select_related('sesion_kinesica', 'pack')
        .order_by('-fecha_registro')
    )
    pagos_recientes = Paginator(pagos_recientes_qs, 5).get_page(request.GET.get('page_pagos', 1))

    registrar_auditoria(request, 'consulta_pagos', paciente=paciente, detalle='Historial de pagos del paciente')

    ctx = {
        'paciente': paciente,
        'clinica': clinica,
        'config': config,
        'pack_activo': resumen.get('pack_activo'),
        'deuda': resumen.get('deuda'),
        'tiene_deuda': resumen.get('tiene_deuda'),
        'pagos_recientes': pagos_recientes,
        'packs_historico': packs_historico,
        'medios_pago': RegistroPago.MEDIOS_PAGO,
        'estados_pago': RegistroPago.ESTADOS,
        'puede_gestionar': _puede_gestionar_pagos(request),
    }
    return render(request, 'pagos/detalle_paciente_pagos.html', ctx)


# ────────────────────────────────────────────
# Registrar pago (Deprecado: redirige a la ficha del paciente o dashboard)
# ────────────────────────────────────────────

@requiere_clinico
def registrar_pago_view(request):
    rut = request.GET.get('rut') or request.POST.get('rut', '')
    if rut:
        return redirect(f'/pagos/paciente/?rut={rut}')
    return redirect('pagos:dashboard')



# ────────────────────────────────────────────
# Registrar Nueva Sesión (Pagar, Pack o Deuda)
# ────────────────────────────────────────────

@requiere_clinico
@require_http_methods(['POST'])
def registrar_nueva_sesion_view(request):
    """
    Registra una nueva sesión clínica para el paciente y permite:
    - Descontarla de un pack activo
    - Pagarla de inmediato (con medio de pago)
    - Dejarla como deuda pendiente
    """
    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('pagos:dashboard')

    clinica = _clinica_activa(request)
    if not clinica:
        messages.error(request, 'No tienes una clínica activa.')
        return redirect('panel')

    rut = request.POST.get('rut', '').strip()
    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('pagos:dashboard')

    clinico = _clinico_activo(request)

    from ciclos_clinicos.selectors import obtener_ciclo_activo
    from ciclos_clinicos.services import iniciar_nuevo_ciclo
    ciclo = obtener_ciclo_activo(paciente, clinica.id)
    if not ciclo:
        ciclo = iniciar_nuevo_ciclo(paciente, clinica, clinico, motivo_consulta="Tratamiento Kinesiológico")

    from SesionesKinesicas.models import SesionKinesica
    num_sesion = ciclo.sesiones_kinesicas.count() + 1
    notas = request.POST.get('notas', '').strip()
    modo_pago = request.POST.get('modo_pago', 'deuda')
    pack_activo = services.obtener_pack_activo(paciente, clinica)

    try:
        with transaction.atomic():
            sesion = SesionKinesica.objects.create(
                paciente=paciente,
                ciclo=ciclo,
                clinico=clinico,
                numero_sesion=num_sesion,
                es_primera_sesion=(num_sesion == 1),
                notas_clinicas=notas or f"Sesión #{num_sesion} registrada desde módulo de pagos.",
            )

            if modo_pago == 'pack' and pack_activo:
                if pack_activo.sesiones_disponibles <= 0:
                    raise ValueError('El pack activo no tiene sesiones disponibles.')
                pago = services.consumir_sesion_pack(pack_activo, sesion, clinico)
                registrar_auditoria(
                    request, 'descuento_pack', paciente=paciente,
                    detalle=f'Sesión #{sesion.numero_sesion} descontada del pack {pack_activo.nombre}'
                )
                messages.success(request, f'Sesión #{sesion.numero_sesion} registrada y descontada del pack "{pack_activo.nombre}".')

            elif modo_pago == 'pago_inmediato':
                medio = request.POST.get('medio_pago', RegistroPago.MEDIO_EFECTIVO)
                estado_pago = request.POST.get('estado', RegistroPago.ESTADO_PAGADO)
                import re
                monto_str = request.POST.get('monto', '0')
                monto_str_clean = re.sub(r'\D', '', monto_str)
                monto = int(monto_str_clean) if monto_str_clean else 0
                folio = request.POST.get('folio_bono', '').strip()
                comprobante = request.POST.get('comprobante', '').strip()
                adjunto = request.FILES.get('adjunto')

                # Pago mixto (segundo medio)
                medio_2 = request.POST.get('medio_pago_2', '').strip()
                monto_2_str = re.sub(r'\D', '', request.POST.get('monto_2', '0'))
                try:
                    monto_2 = int(monto_2_str) if monto_2_str else 0
                except ValueError:
                    monto_2 = 0
                comprobante_2 = request.POST.get('comprobante_2', '').strip()

                pago = services.registrar_pago(
                    paciente=paciente,
                    clinica=clinica,
                    sesion_kinesica=sesion,
                    medio_pago=medio,
                    monto=monto,
                    registrado_por=clinico,
                    folio_bono=folio,
                    comprobante=comprobante,
                    estado=estado_pago,
                    notas=notas or f'Pago sesión #{sesion.numero_sesion}',
                    medio_pago_2=medio_2,
                    monto_2=monto_2 if (medio_2 and monto_2 > 0) else 0,
                    comprobante_2=comprobante_2,
                    adjunto=adjunto,
                )
                
                monto_total_pagado = monto + (monto_2 if medio_2 and monto_2 > 0 else 0)
                detalle_auditoria = f'Sesión #{sesion.numero_sesion} pagada — {pago.get_medio_pago_display()} ${monto}'
                if medio_2 and monto_2 > 0:
                    detalle_auditoria += f' + {pago.get_medio_pago_2_display()} ${monto_2}'

                registrar_auditoria(
                    request, 'registro_pago', paciente=paciente,
                    detalle=detalle_auditoria
                )
                messages.success(request, f'Sesión #{sesion.numero_sesion} registrada y pagada (${monto_total_pagado:,.0f}).')

            else:
                # Se registra la sesión como deuda con el monto especificado
                import re
                monto_deuda_str = re.sub(r'\D', '', request.POST.get('monto_deuda', ''))
                config = services.obtener_configuracion(clinica)
                default_val = config.precio_sesion_default if (config.precio_sesion_default and config.precio_sesion_default > 0) else Decimal('25000')
                try:
                    monto_deuda = Decimal(monto_deuda_str) if monto_deuda_str else Decimal(str(default_val))
                except Exception:
                    monto_deuda = Decimal(str(default_val))

                RegistroPago.objects.create(
                    paciente=paciente,
                    clinica=clinica,
                    sesion_kinesica=sesion,
                    medio_pago=RegistroPago.MEDIO_EFECTIVO,
                    monto=monto_deuda,
                    estado=RegistroPago.ESTADO_PENDIENTE,
                    registrado_por=clinico,
                    notas=notas or f'Sesión #{sesion.numero_sesion} registrada como deuda pendiente',
                )
                services.recalcular_deuda(paciente, clinica)
                registrar_auditoria(
                    request, 'registro_sesion', paciente=paciente,
                    detalle=f'Sesión #{sesion.numero_sesion} registrada como deuda pendiente (${monto_deuda:,.0f})'
                )
                messages.success(request, f'Sesión #{sesion.numero_sesion} registrada correctamente como deuda pendiente (${monto_deuda:,.0f}).')

    except Exception as e:
        messages.error(request, f'Error al registrar la sesión: {e}')

    return redirect(f'/pagos/paciente/?rut={rut}')


# ────────────────────────────────────────────
# Gestión de Packs
# ────────────────────────────────────────────

@requiere_clinico
@require_http_methods(['GET', 'POST'])
def crear_pack_view(request):
    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para crear packs.')
        return redirect('pagos:dashboard')

    clinica = _clinica_activa(request)
    if not clinica:
        messages.error(request, 'No tienes una clínica activa.')
        return redirect('panel')

    rut = request.GET.get('rut') or request.POST.get('rut', '')
    paciente = None
    if rut:
        paciente = obtener_paciente_por_rut(request, rut)

    if request.method == 'POST':
        if '_buscar' in request.POST:
            rut = request.POST.get('rut', '').strip()
            return redirect(f'{request.path}?rut={rut}')
            
        rut = request.POST.get('rut', '').strip()
        paciente = obtener_paciente_por_rut(request, rut)
        if not paciente:
            messages.error(request, 'Paciente no encontrado.')
        else:
            nombre = request.POST.get('nombre', '').strip()
            total_raw = request.POST.get('total_sesiones', '0').strip()
            precio_raw = request.POST.get('precio_total', '0').replace(',', '').replace('.', '').strip()
            vencimiento_raw = request.POST.get('fecha_vencimiento', '').strip() or None
            notas = request.POST.get('notas', '').strip()

            try:
                total_sesiones = int(total_raw)
                precio = int(precio_raw) if precio_raw else 0
            except ValueError:
                messages.error(request, 'Número de sesiones o precio inválidos.')
                total_sesiones = 0

            medio_pago = request.POST.get('medio_pago', '')
            pack_activo = services.obtener_pack_activo(paciente, clinica)

            if pack_activo:
                # Regla de negocio: todos los pack deben acumularse si hay uno ya activo
                if total_sesiones < 1:
                    messages.error(request, 'Debes ingresar al menos 1 sesión para acumular al pack.')
                else:
                    clinico = _clinico_activo(request)
                    estado_pago = request.POST.get('estado', RegistroPago.ESTADO_PAGADO)
                    folio = request.POST.get('folio_bono', '').strip()
                    comprobante = request.POST.get('comprobante', '').strip()
                    adjunto = request.FILES.get('adjunto')

                    pack = services.acumular_sesiones_pack(
                        pack=pack_activo,
                        sesiones_extra=total_sesiones,
                        precio_extra=precio,
                        registrado_por=clinico,
                        medio_pago=medio_pago,
                        notas=notas,
                        folio_bono=folio,
                        comprobante=comprobante,
                        estado=estado_pago,
                        adjunto=adjunto,
                    )
                    registrar_auditoria(
                        request, 'recarga_pack', paciente=paciente,
                        detalle=f'Pack: {pack.nombre} +{total_sesiones} sesiones — ${precio}',
                    )
                    messages.success(request, f'Se acumularon {total_sesiones} sesiones al pack activo "{pack.nombre}". Total disponibles: {pack.sesiones_disponibles}.')
                    return redirect(f'/pagos/paciente/?rut={rut}')
            else:
                # No hay pack activo: crear uno nuevo
                if not nombre:
                    messages.error(request, 'El nombre del pack es obligatorio.')
                elif total_sesiones < 1:
                    messages.error(request, 'El pack debe tener al menos 1 sesión.')
                else:
                    from datetime import date
                    fecha_venc = None
                    if vencimiento_raw:
                        try:
                            fecha_venc = date.fromisoformat(vencimiento_raw)
                        except ValueError:
                            fecha_venc = None

                    clinico = _clinico_activo(request)
                    estado_pago = request.POST.get('estado', RegistroPago.ESTADO_PAGADO)
                    folio = request.POST.get('folio_bono', '').strip()
                    comprobante = request.POST.get('comprobante', '').strip()
                    adjunto = request.FILES.get('adjunto')

                    pack = services.crear_pack(
                        paciente=paciente,
                        clinica=clinica,
                        nombre=nombre,
                        total_sesiones=total_sesiones,
                        precio=precio,
                        registrado_por=clinico,
                        medio_pago=medio_pago,
                        fecha_vencimiento=fecha_venc,
                        notas=notas,
                        folio_bono=folio,
                        comprobante=comprobante,
                        estado=estado_pago,
                        adjunto=adjunto,
                    )
                    registrar_auditoria(
                        request, 'creacion_pack', paciente=paciente,
                        detalle=f'Pack: {pack.nombre} — {pack.total_sesiones} sesiones — ${pack.precio_total}',
                    )
                    messages.success(request, f'Pack "{pack.nombre}" creado exitosamente.')
                    return redirect(f'/pagos/paciente/?rut={rut}')

    ctx = {
        'paciente': paciente,
        'clinica': clinica,
        'rut': rut,
        'medios_pago': RegistroPago.MEDIOS_PAGO,
        'estados_pago': RegistroPago.ESTADOS,
        'pack_activo': services.obtener_pack_activo(paciente, clinica) if paciente else None,
    }
    return render(request, 'pagos/gestionar_pack.html', ctx)


@requiere_clinico
def detalle_pack_view(request, pack_id):
    clinica = _clinica_activa(request)
    pack = get_object_or_404(PackAtencion, id=pack_id, clinica=clinica)
    pagos_pack_qs = (
        RegistroPago.objects.filter(pack=pack)
        .exclude(estado=RegistroPago.ESTADO_ANULADO)
        .order_by('-fecha_registro')
    )
    pagos_pack = Paginator(pagos_pack_qs, 5).get_page(request.GET.get('page', 1))
    ctx = {
        'pack': pack,
        'pagos_pack': pagos_pack,
        'clinica': clinica,
    }
    return render(request, 'pagos/detalle_pack.html', ctx)


# ────────────────────────────────────────────
# APIs JSON
# ────────────────────────────────────────────

@requiere_clinico
def api_estado_pago(request, rut):
    """Retorna el estado de deuda del paciente (para badges en ficha)."""
    clinica = _clinica_activa(request)
    if not clinica:
        return JsonResponse({'error': 'Sin clínica activa'}, status=403)

    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)

    deuda = services.obtener_deuda(paciente, clinica)
    pack = services.obtener_pack_activo(paciente, clinica)

    return JsonResponse({
        'tiene_deuda': deuda.tiene_deuda if deuda else False,
        'sesiones_sin_pago': deuda.sesiones_sin_pago if deuda else 0,
        'monto_pendiente': float(deuda.monto_pendiente) if deuda else 0,
        'bonos_por_llegar': deuda.bonos_por_llegar if deuda else 0,
        'tiene_pack_activo': bool(pack),
        'pack_sesiones_disponibles': pack.sesiones_disponibles if pack else 0,
        'pack_nombre': pack.nombre if pack else None,
    })


@requiere_clinico
def api_resumen_financiero(request):
    """Métricas financieras del centro (solo admin_clinica)."""
    if not request.session.get('es_admin_clinica') and not request.session.get('es_admin'):
        return JsonResponse({'error': 'Sin permisos'}, status=403)

    clinica = _clinica_activa(request)
    if not clinica:
        return JsonResponse({'error': 'Sin clínica activa'}, status=403)

    resumen = services.obtener_resumen_financiero_clinica(clinica)
    resumen['ingresos_mes'] = float(resumen['ingresos_mes'])
    return JsonResponse(resumen)


# ────────────────────────────────────────────
# Anular pago
# ────────────────────────────────────────────

@requiere_clinico
@require_POST
def anular_pago_view(request, pago_id):
    if not _puede_gestionar_pagos(request):
        return JsonResponse({'error': 'Sin permisos'}, status=403)

    clinica = _clinica_activa(request)
    pago = get_object_or_404(RegistroPago, id=pago_id, clinica=clinica)
    clinico = _clinico_activo(request)

    try:
        services.anular_pago(pago, clinico)
        registrar_auditoria(
            request,
            'anulacion_pago',
            paciente=pago.paciente,
            detalle=f'Pago #{pago.id} anulado — {pago.get_medio_pago_display()}',
        )
        messages.success(request, 'Pago anulado correctamente.')
    except ValueError as e:
        messages.error(request, str(e))

    rut = pago.paciente.rut
    return redirect(f'/pagos/paciente/?rut={rut}')


# ────────────────────────────────────────────
# Editar pago
# ────────────────────────────────────────────

@requiere_clinico
def editar_pago_view(request, pago_id):
    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para editar pagos.')
        return redirect('pagos:dashboard')

    clinica = _clinica_activa(request)
    pago = get_object_or_404(RegistroPago, id=pago_id, clinica=clinica)

    if request.method == 'POST':
        import re
        monto_str = re.sub(r'\D', '', str(request.POST.get('monto', 0)))
        monto = int(monto_str) if monto_str else 0
        medio_pago = request.POST.get('medio_pago')
        estado = request.POST.get('estado')
        folio = request.POST.get('folio_bono', '').strip()
        comprobante = request.POST.get('comprobante', '').strip()
        notas = request.POST.get('notas', '').strip()

        medio_pago_2 = request.POST.get('medio_pago_2', '').strip()
        monto_2_str = re.sub(r'\D', '', str(request.POST.get('monto_2', 0)))
        monto_2 = int(monto_2_str) if monto_2_str else 0
        comprobante_2 = request.POST.get('comprobante_2', '').strip()
        adjunto = request.FILES.get('adjunto')

        try:
            services.editar_pago(
                pago, monto, medio_pago, estado, folio, comprobante, notas,
                medio_pago_2=medio_pago_2, monto_2=monto_2, comprobante_2=comprobante_2,
                adjunto=adjunto
            )
            registrar_auditoria(
                request,
                'edicion_pago',
                paciente=pago.paciente,
                detalle=f'Editó el pago #{pago.id}',
            )
            messages.success(request, 'Pago actualizado correctamente.')
            return redirect(f'/pagos/paciente/?rut={pago.paciente.rut}')
        except Exception as e:
            messages.error(request, f'Error al actualizar el pago: {e}')

    ctx = {
        'pago': pago,
        'paciente': pago.paciente,
        'medios_pago': RegistroPago.MEDIOS_PAGO,
        'estados_pago': RegistroPago.ESTADOS,
        'es_edicion': True,
    }
    return render(request, 'pagos/editar_pago.html', ctx)

# ────────────────────────────────────────────
# Acciones 1-Clic
# ────────────────────────────────────────────

@requiere_clinico
@require_POST
def pago_masivo_view(request):
    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para gestionar pagos.')
        return redirect('pagos:dashboard')
        
    rut = request.POST.get('rut', '').strip()
    paciente = obtener_paciente_por_rut(request, rut)
    if not paciente:
        messages.error(request, 'Paciente no encontrado.')
        return redirect('pagos:dashboard')

    clinica = _clinica_activa(request)
    clinico = _clinico_activo(request)

    services.recalcular_deuda(paciente, clinica)
    deuda = services.obtener_deuda(paciente, clinica)
    tiene_deuda = bool(deuda and (deuda.monto_pendiente > 0 or deuda.sesiones_sin_pago > 0))
    if not tiene_deuda:
        messages.error(request, f'El paciente {paciente.nombre} {paciente.apellido} no tiene deudas pendientes que pagar.')
        return redirect(f'/pagos/paciente/?rut={paciente.rut}')
        
    import re
    monto_str = request.POST.get('monto_total', '0')
    monto_str_clean = re.sub(r'\D', '', monto_str)
    monto = int(monto_str_clean) if monto_str_clean.isdigit() else 0
    medio_pago = request.POST.get('medio_pago', RegistroPago.MEDIO_EFECTIVO)
    estado = request.POST.get('estado', RegistroPago.ESTADO_PAGADO)
    folio_bono = request.POST.get('folio_bono', '').strip()
    comprobante = request.POST.get('comprobante', '').strip()
    notas = request.POST.get('notas', '').strip()
    adjunto = request.FILES.get('adjunto')

    # Soporte pago mixto si fue enviado
    medio_2 = request.POST.get('medio_pago_2', '').strip()
    monto_2_str = re.sub(r'\D', '', request.POST.get('monto_2', '0'))
    monto_2 = int(monto_2_str) if monto_2_str else 0
    comprobante_2 = request.POST.get('comprobante_2', '').strip()

    monto_total_ingresado = monto + (monto_2 if medio_2 and monto_2 > 0 else 0)
    
    try:
        if monto_total_ingresado > 0:
            services.pago_masivo_deuda(
                paciente=paciente,
                clinica=clinica,
                monto_total=monto_total_ingresado,
                medio_pago=medio_pago,
                registrado_por=clinico,
                folio_bono=folio_bono,
                notas=notas,
                medio_pago_2=medio_2,
                monto_2=monto_2 if (medio_2 and monto_2 > 0) else 0,
                comprobante_2=comprobante_2,
                comprobante=comprobante,
                monto_1=monto,
                adjunto=adjunto,
                estado=estado,
            )
            detalle = f'Pago masivo de Deuda: ${monto_total_ingresado}'
            if medio_2 and monto_2 > 0:
                detalle += f' (Mixto: ${monto} con {medio_pago} + ${monto_2} con {medio_2})'
            registrar_auditoria(request, 'pago_masivo', paciente=paciente, detalle=detalle)
            messages.success(request, f'Se ha registrado el pago de la deuda correctamente por ${monto_total_ingresado:,.0f}.')
        else:
            messages.error(request, 'El monto debe ser mayor a 0.')
    except Exception as e:
        messages.error(request, f'Error al procesar el pago masivo: {e}')
        
    return redirect(f'/pagos/paciente/?rut={paciente.rut}')

@requiere_clinico
@require_POST
def descontar_pack_rapido_view(request, sesion_id):
    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para gestionar pagos.')
        return redirect('pagos:dashboard')
        
    rut = request.POST.get('rut', '').strip()
    paciente = obtener_paciente_por_rut(request, rut)

    # ── Protección anti double-submit ─────────────────────────────────
    import time
    lock_key = f'_pack_descuento_{rut}'
    last_ts = request.session.get(lock_key, 0)
    now_ts = time.time()
    if now_ts - last_ts < 3:  # bloquear si pasaron menos de 3 segundos
        messages.error(request, 'Operación demasiado rápida. Espera un momento antes de volver a descontar.')
        if paciente:
            return redirect(f'/pagos/paciente/?rut={paciente.rut}')
        return redirect('pagos:dashboard')
    request.session[lock_key] = now_ts
    # ─────────────────────────────────────────────────────────────────
    
    try:
        clinica = _clinica_activa(request)
        clinico = _clinico_activo(request)
        
        # Si sesion_id es 0, significa que es un descuento genérico (la más antigua)
        target_sesion = None if sesion_id == 0 else sesion_id
        
        services.descontar_pack_rapido(paciente, clinica, clinico, sesion_id=target_sesion)
        if paciente:
            registrar_auditoria(request, 'descuento_pack_rapido', paciente=paciente, detalle=f'Sesión descontada del pack ({sesion_id})')
        messages.success(request, 'Sesión descontada del pack exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al descontar del pack: {e}')
        
    if paciente:
        return redirect(f'/pagos/paciente/?rut={paciente.rut}')
    return redirect('pagos:dashboard')



# ────────────────────────────────────────────
# Eliminar pago definitivo
# ────────────────────────────────────────────

@requiere_clinico
@require_POST
def eliminar_pago_view(request, pago_id):
    if not _puede_gestionar_pagos(request):
        return JsonResponse({'error': 'Sin permisos'}, status=403)

    clinica = _clinica_activa(request)
    pago = get_object_or_404(RegistroPago, id=pago_id, clinica=clinica)
    clinico = _clinico_activo(request)
    rut = pago.paciente.rut

    try:
        services.eliminar_pago_definitivo(pago, clinico)
        registrar_auditoria(
            request,
            'eliminacion_pago',
            paciente=pago.paciente,
            detalle=f'Pago #{pago_id} eliminado definitivamente',
        )
        messages.success(request, 'Pago eliminado físicamente del sistema.')
    except Exception as e:
        messages.error(request, f'Error al eliminar el pago: {e}')

    return redirect(f'/pagos/paciente/?rut={rut}')
