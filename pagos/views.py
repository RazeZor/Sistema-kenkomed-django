from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

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

    # Pacientes con deuda para la tabla principal
    deudas_qs = (
        DeudaPaciente.objects.filter(clinica=clinica)
        .filter(sesiones_sin_pago__gt=0)
        .select_related('paciente')
        .order_by('-sesiones_sin_pago', '-monto_pendiente')
    )

    # Pagos recientes del centro
    pagos_recientes = (
        RegistroPago.objects.filter(clinica=clinica)
        .exclude(estado=RegistroPago.ESTADO_ANULADO)
        .select_related('paciente', 'registrado_por', 'sesion_kinesica', 'pack')
        .order_by('-fecha_registro')[:20]
    )

    # Packs activos
    packs_activos = (
        PackAtencion.objects.filter(clinica=clinica, estado=PackAtencion.ESTADO_ACTIVO)
        .select_related('paciente')
        .order_by('-fecha_compra')[:10]
    )

    registrar_auditoria(request, 'consulta_pagos', detalle='Dashboard de pagos del centro')

    ctx = {
        'clinica': clinica,
        'resumen': resumen,
        'deudas': deudas_qs,
        'pagos_recientes': pagos_recientes,
        'packs_activos': packs_activos,
        'hoy': timezone.localdate(),
        'medios_pago': RegistroPago.MEDIOS_PAGO,
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

    resumen = services.obtener_resumen_financiero_paciente(paciente, clinica)
    config = services.obtener_configuracion(clinica)

    registrar_auditoria(request, 'consulta_pagos', paciente=paciente, detalle='Historial de pagos del paciente')

    ctx = {
        'paciente': paciente,
        'clinica': clinica,
        'config': config,
        **resumen,
        'medios_pago': RegistroPago.MEDIOS_PAGO,
        'estados_pago': RegistroPago.ESTADOS,
        'puede_gestionar': _puede_gestionar_pagos(request),
    }
    return render(request, 'pagos/detalle_paciente_pagos.html', ctx)


# ────────────────────────────────────────────
# Registrar pago
# ────────────────────────────────────────────

@requiere_clinico
@require_http_methods(['GET', 'POST'])
def registrar_pago_view(request):
    if not _puede_gestionar_pagos(request):
        messages.error(request, 'No tienes permisos para registrar pagos.')
        return redirect('pagos:dashboard')

    clinica = _clinica_activa(request)
    if not clinica:
        messages.error(request, 'No tienes una clínica activa.')
        return redirect('panel')

    config = services.obtener_configuracion(clinica)

    rut = request.GET.get('rut') or request.POST.get('rut', '')
    paciente = None
    pack_activo = None

    if rut:
        paciente = obtener_paciente_por_rut(request, rut)
        if paciente:
            pack_activo = services.obtener_pack_activo(paciente, clinica)

    if request.method == 'POST':
        if '_buscar' in request.POST:
            rut = request.POST.get('rut', '').strip()
            return redirect(f'{request.path}?rut={rut}')
            
        rut = request.POST.get('rut', '').strip()
        paciente = obtener_paciente_por_rut(request, rut)
        if not paciente:
            messages.error(request, 'Paciente no encontrado.')
        else:
            medio = request.POST.get('medio_pago', '')
            import re
            monto_str = request.POST.get('monto', '0')
            monto_str_clean = re.sub(r'\D', '', monto_str)
            try:
                monto = int(monto_str_clean) if monto_str_clean else 0
            except ValueError:
                monto = 0

            estado = request.POST.get('estado', RegistroPago.ESTADO_PAGADO)
            folio = request.POST.get('folio_bono', '').strip()
            comprobante = request.POST.get('comprobante', '').strip()
            notas = request.POST.get('notas', '').strip()
            usar_pack = request.POST.get('usar_pack') == '1'

            clinico = _clinico_activo(request)

            try:
                if usar_pack and pack_activo:
                    # Descuenta del pack
                    pago = services.consumir_sesion_pack(pack_activo, None, clinico)
                else:
                    pago = services.registrar_pago(
                        paciente=paciente,
                        clinica=clinica,
                        medio_pago=medio,
                        monto=monto,
                        registrado_por=clinico,
                        folio_bono=folio,
                        comprobante=comprobante,
                        estado=estado,
                        notas=notas,
                    )

                registrar_auditoria(
                    request,
                    'registro_pago',
                    paciente=paciente,
                    detalle=f'{pago.get_medio_pago_display()} — ${pago.monto} — {pago.get_estado_display()}',
                )
                messages.success(request, f'Pago registrado correctamente ({pago.get_medio_pago_display()}).')
                return redirect(f'{request.path}?rut={rut}')

            except Exception as e:
                messages.error(request, f'Error al registrar el pago: {e}')

    ctx = {
        'paciente': paciente,
        'clinica': clinica,
        'config': config,
        'pack_activo': pack_activo,
        'medios_pago': RegistroPago.MEDIOS_PAGO,
        'estados_pago': RegistroPago.ESTADOS,
        'rut': rut,
    }
    return render(request, 'pagos/registrar_pago.html', ctx)


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

                medio_pago = request.POST.get('medio_pago', '')
                clinico = _clinico_activo(request)
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
                )
                registrar_auditoria(
                    request,
                    'creacion_pack',
                    paciente=paciente,
                    detalle=f'Pack: {pack.nombre} — {pack.total_sesiones} sesiones — ${pack.precio_total}',
                )
                messages.success(request, f'Pack "{pack.nombre}" creado exitosamente.')
                return redirect(f'/pagos/paciente/?rut={rut}')

    ctx = {
        'paciente': paciente,
        'clinica': clinica,
        'rut': rut,
        'medios_pago': RegistroPago.MEDIOS_PAGO,
    }
    return render(request, 'pagos/gestionar_pack.html', ctx)


@requiere_clinico
def detalle_pack_view(request, pack_id):
    clinica = _clinica_activa(request)
    pack = get_object_or_404(PackAtencion, id=pack_id, clinica=clinica)
    pagos_pack = (
        RegistroPago.objects.filter(pack=pack)
        .exclude(estado=RegistroPago.ESTADO_ANULADO)
        .order_by('-fecha_registro')
    )
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
        monto = request.POST.get('monto', 0)
        medio_pago = request.POST.get('medio_pago')
        estado = request.POST.get('estado')
        folio = request.POST.get('folio_bono', '')
        comprobante = request.POST.get('comprobante', '')
        notas = request.POST.get('notas', '')

        try:
            services.editar_pago(pago, monto, medio_pago, estado, folio, comprobante, notas)
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
    return render(request, 'pagos/registrar_pago.html', ctx)

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
        
    import re
    monto_str = request.POST.get('monto_total', '0')
    monto_str_clean = re.sub(r'\D', '', monto_str)
    monto = int(monto_str_clean) if monto_str_clean.isdigit() else 0
    medio_pago = request.POST.get('medio_pago', RegistroPago.MEDIO_EFECTIVO)
    folio_bono = request.POST.get('folio_bono', '').strip()
    notas = request.POST.get('notas', '').strip()
    
    try:
        clinica = _clinica_activa(request)
        clinico = _clinico_activo(request)
        if monto > 0:
            services.pago_masivo_deuda(
                paciente=paciente,
                clinica=clinica,
                monto_total=monto,
                medio_pago=medio_pago,
                registrado_por=clinico,
                folio_bono=folio_bono,
                notas=notas
            )
            registrar_auditoria(request, 'pago_masivo', paciente=paciente, detalle=f'Pago masivo de Deuda: ${monto}')
            messages.success(request, f'Se ha saldado la deuda correctamente por ${monto}.')
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
