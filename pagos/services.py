"""
Lógica de negocio del módulo de pagos.
Todas las funciones son puras y no acceden a request directamente.
"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from .models import PackAtencion, RegistroPago, DeudaPaciente, ConfiguracionPagos


# ────────────────────────────────────────────
# Packs de Atención
# ────────────────────────────────────────────

def obtener_pack_activo(paciente, clinica):
    """Retorna el pack activo más reciente del paciente en la clínica, o None."""
    return (
        PackAtencion.objects.filter(
            paciente=paciente,
            clinica=clinica,
            estado=PackAtencion.ESTADO_ACTIVO,
        )
        .order_by('-fecha_compra')
        .first()
    )


def crear_pack(paciente, clinica, nombre, total_sesiones, precio, registrado_por, medio_pago=None, fecha_vencimiento=None, notas=''):
    """Crea un nuevo pack de atenciones para un paciente y registra el ingreso."""
    with transaction.atomic():
        pack = PackAtencion.objects.create(
            paciente=paciente,
            clinica=clinica,
            nombre=nombre,
            total_sesiones=total_sesiones,
            precio_total=Decimal(str(precio)),
            registrado_por=registrado_por,
            fecha_vencimiento=fecha_vencimiento,
            notas=notas,
        )
        # Crear el pago para que cuadre en la caja inmediatamente
        if pack.precio_total > 0 and medio_pago:
            RegistroPago.objects.create(
                paciente=paciente,
                clinica=clinica,
                pack=pack,
                medio_pago=medio_pago,
                monto=pack.precio_total,
                estado=RegistroPago.ESTADO_PAGADO,
                registrado_por=registrado_por,
                notas=f'Pago por compra de pack: {pack.nombre}',
            )
    return pack


def consumir_sesion_pack(pack, sesion_kinesica, registrado_por):
    """
    Descuenta una sesión del pack y registra el pago correspondiente.
    Retorna el RegistroPago creado.
    Lanza ValueError si el pack no tiene sesiones disponibles.
    """
    if pack.sesiones_disponibles <= 0:
        raise ValueError('El pack no tiene sesiones disponibles.')

    with transaction.atomic():
        # Bloquear fila para evitar concurrencia
        pack = PackAtencion.objects.select_for_update().get(id=pack.id)
        if pack.sesiones_disponibles <= 0:
            raise ValueError('El pack no tiene sesiones disponibles.')

        pack.sesiones_usadas += 1
        if pack.sesiones_usadas >= pack.total_sesiones:
            pack.estado = PackAtencion.ESTADO_AGOTADO
        pack.save(update_fields=['sesiones_usadas', 'estado'])

        pago = RegistroPago.objects.create(
            paciente=pack.paciente,
            clinica=pack.clinica,
            sesion_kinesica=sesion_kinesica,
            pack=pack,
            medio_pago=RegistroPago.MEDIO_PACK,
            monto=0,  # El monto ya fue pagado al comprar el pack
            estado=RegistroPago.ESTADO_PAGADO,
            registrado_por=registrado_por,
            notas=f'Sesión descontada del pack: {pack.nombre}',
        )

    recalcular_deuda(pack.paciente, pack.clinica)
    return pago


def verificar_vencimiento_packs(clinica):
    """Marca como vencidos los packs cuya fecha de vencimiento ya pasó."""
    hoy = timezone.localdate()
    vencidos = PackAtencion.objects.filter(
        clinica=clinica,
        estado=PackAtencion.ESTADO_ACTIVO,
        fecha_vencimiento__lt=hoy,
    )
    count = vencidos.update(estado=PackAtencion.ESTADO_VENCIDO)
    return count


def descontar_pack_rapido(paciente, clinica, registrado_por, sesion_id=None):
    """Descuenta la sesión huérfana más antigua (o una específica) de un pack activo en 1 clic."""
    pack = obtener_pack_activo(paciente, clinica)
    if not pack:
        raise ValueError("El paciente no tiene un pack activo.")
        
    from SesionesKinesicas.models import SesionKinesica
    if sesion_id:
        sesion = SesionKinesica.objects.filter(id=sesion_id, paciente=paciente).first()
    else:
        # Buscar la más antigua huérfana
        pagos_activos = RegistroPago.objects.filter(
            paciente=paciente, clinica=clinica
        ).exclude(estado=RegistroPago.ESTADO_ANULADO)
        
        sesiones_con_pago = pagos_activos.filter(
            sesion_kinesica__isnull=False
        ).values_list('sesion_kinesica_id', flat=True)
        
        sesion = SesionKinesica.objects.filter(
            paciente=paciente, ciclo__clinica=clinica
        ).exclude(id__in=sesiones_con_pago).order_by('fecha_creacion').first()
        
    # Se permite descontar 'al aire' si no hay sesiones huérfanas aún
    return consumir_sesion_pack(pack, sesion, registrado_por)


# ────────────────────────────────────────────
# Registro de Pagos
# ────────────────────────────────────────────

def registrar_pago(
    paciente,
    clinica,
    medio_pago,
    monto,
    registrado_por,
    sesion_kinesica=None,
    pack=None,
    folio_bono='',
    comprobante='',
    estado=RegistroPago.ESTADO_PAGADO,
    notas='',
):
    """Registra un pago individual. Recalcula la deuda al terminar."""
    pago = RegistroPago.objects.create(
        paciente=paciente,
        clinica=clinica,
        sesion_kinesica=sesion_kinesica,
        pack=pack,
        medio_pago=medio_pago,
        monto=Decimal(str(monto)),
        folio_bono=folio_bono,
        comprobante=comprobante,
        estado=estado,
        registrado_por=registrado_por,
        notas=notas,
    )
    recalcular_deuda(paciente, clinica)
    return pago


def anular_pago(pago, registrado_por):
    """Anula un registro de pago. Si era de pack, devuelve la sesión."""
    with transaction.atomic():
        if pago.estado == RegistroPago.ESTADO_ANULADO:
            raise ValueError('El pago ya está anulado.')

        if pago.medio_pago == RegistroPago.MEDIO_PACK and pago.pack:
            # Bloquear fila para devolución
            pack = PackAtencion.objects.select_for_update().get(id=pago.pack.id)
            if pack.sesiones_usadas > 0:
                pack.sesiones_usadas -= 1
                pack.estado = PackAtencion.ESTADO_ACTIVO
                pack.save(update_fields=['sesiones_usadas', 'estado'])

        pago.estado = RegistroPago.ESTADO_ANULADO
        pago.notas = (pago.notas + f' | Anulado por {registrado_por.nombre} {registrado_por.apellido}').strip()
        pago.save(update_fields=['estado', 'notas'])

    recalcular_deuda(pago.paciente, pago.clinica)
    return pago


def pago_masivo_deuda(paciente, clinica, monto_total, medio_pago, registrado_por, folio_bono='', notas=''):
    """Liquida o abona a las sesiones con deuda usando un solo pago."""
    from SesionesKinesicas.models import SesionKinesica
    from django.db.models import Sum
    
    monto_ingresado = Decimal(str(monto_total))
    if monto_ingresado <= 0:
        return False
        
    with transaction.atomic():
        pagos_activos = RegistroPago.objects.filter(
            paciente=paciente, clinica=clinica
        ).exclude(estado=RegistroPago.ESTADO_ANULADO)
        
        config = obtener_configuracion(clinica)
        precio_default = config.precio_sesion_default
        
        monto_restante = monto_ingresado
        
        # 1. Intentar saldar pagos explícitos 'Pendientes'
        pagos_pendientes = pagos_activos.filter(
            estado__in=[RegistroPago.ESTADO_PENDIENTE, RegistroPago.ESTADO_BONO_POR_LLEGAR]
        ).order_by('fecha_registro')
        
        for p in pagos_pendientes:
            if monto_restante <= 0:
                break
            monto_aplicar = min(monto_restante, p.monto if p.monto > 0 else precio_default)
            if monto_aplicar >= p.monto:
                p.estado = RegistroPago.ESTADO_PAGADO
                p.medio_pago = medio_pago
                if folio_bono: p.folio_bono = folio_bono
                p.notas = (p.notas + f" | Saldado masivamente. {notas}").strip()
                p.save(update_fields=['estado', 'medio_pago', 'folio_bono', 'notas'])
                monto_restante -= p.monto
            else:
                RegistroPago.objects.create(
                    paciente=paciente, clinica=clinica, sesion_kinesica=p.sesion_kinesica,
                    pack=p.pack, medio_pago=medio_pago, monto=monto_aplicar,
                    estado=RegistroPago.ESTADO_PAGADO, folio_bono=folio_bono,
                    registrado_por=registrado_por, notas=f"Abono parcial a deuda. {notas}".strip()
                )
                p.monto -= monto_aplicar
                p.save(update_fields=['monto'])
                monto_restante = Decimal('0')

        # 2. Buscar sesiones con deuda (huérfanas o parcialmente pagadas)
        sesiones = SesionKinesica.objects.filter(
            paciente=paciente, ciclo__clinica=clinica
        ).order_by('fecha_creacion')
        
        for sesion in sesiones:
            if monto_restante <= 0:
                break
                
            pagos_sesion = pagos_activos.filter(sesion_kinesica=sesion)
            if pagos_sesion.filter(medio_pago=RegistroPago.MEDIO_PACK).exists():
                continue
                
            pagado = pagos_sesion.filter(estado__in=[RegistroPago.ESTADO_PAGADO, RegistroPago.ESTADO_BONO_POR_LLEGAR]).aggregate(total=Sum('monto'))['total'] or Decimal('0')
            deuda_sesion = precio_default - pagado
            
            if deuda_sesion > 0:
                monto_aplicar = min(monto_restante, deuda_sesion)
                RegistroPago.objects.create(
                    paciente=paciente, clinica=clinica, sesion_kinesica=sesion,
                    medio_pago=medio_pago, monto=monto_aplicar,
                    estado=RegistroPago.ESTADO_PAGADO, folio_bono=folio_bono,
                    registrado_por=registrado_por, notas=f"Abono automático. {notas}".strip()
                )
                monto_restante -= monto_aplicar
                
        # 3. Si sobró plata (Abono Libre a favor del paciente)
        if monto_restante > 0:
            RegistroPago.objects.create(
                paciente=paciente, clinica=clinica, sesion_kinesica=None,
                medio_pago=medio_pago, monto=monto_restante,
                estado=RegistroPago.ESTADO_PAGADO, folio_bono=folio_bono,
                registrado_por=registrado_por, notas=f"Abono libre a favor. {notas}".strip()
            )
            
    recalcular_deuda(paciente, clinica)
    return True


# ────────────────────────────────────────────
# Deuda
# ────────────────────────────────────────────

def recalcular_deuda(paciente, clinica):
    """
    Recalcula el resumen de deuda del paciente evaluando micromorososidades por sesión.
    """
    from SesionesKinesicas.models import SesionKinesica
    from django.db.models import Sum

    pagos_activos = RegistroPago.objects.filter(
        paciente=paciente,
        clinica=clinica,
    ).exclude(estado=RegistroPago.ESTADO_ANULADO)

    total_sesiones = SesionKinesica.objects.filter(
        paciente=paciente,
        ciclo__clinica=clinica
    )

    config = obtener_configuracion(clinica)
    precio_default = config.precio_sesion_default

    # 1. Abonos Libres (Pagos sin sesión y sin pack)
    abonos_libres = pagos_activos.filter(
        sesion_kinesica__isnull=True,
        pack__isnull=True,
        estado=RegistroPago.ESTADO_PAGADO
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    # 2. Deuda explícita sin sesión (Registros manuales pendientes)
    deuda_explicita_sin_sesion = pagos_activos.filter(
        sesion_kinesica__isnull=True,
        pack__isnull=True,
        estado__in=[RegistroPago.ESTADO_PENDIENTE, RegistroPago.ESTADO_BONO_POR_LLEGAR]
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    # 3. Calcular deuda sesión por sesión
    monto_pendiente_sesiones = Decimal('0')
    sesiones_sin_pago_completo = 0

    for sesion in total_sesiones:
        pagos_sesion = pagos_activos.filter(sesion_kinesica=sesion)
        
        if pagos_sesion.filter(medio_pago=RegistroPago.MEDIO_PACK).exists():
            continue
            
        pagado_a_sesion = pagos_sesion.filter(
            estado__in=[RegistroPago.ESTADO_PAGADO, RegistroPago.ESTADO_BONO_POR_LLEGAR]
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        deuda_sesion = precio_default - pagado_a_sesion
        
        if deuda_sesion > 0:
            monto_pendiente_sesiones += deuda_sesion
            sesiones_sin_pago_completo += 1
        elif deuda_sesion < 0:
            # Sobrepago: el exceso se suma a los abonos libres
            abonos_libres += abs(deuda_sesion)

    # 4. Cálculo final
    monto_pendiente_total = monto_pendiente_sesiones + deuda_explicita_sin_sesion - abonos_libres
    
    bonos_por_llegar = pagos_activos.filter(estado=RegistroPago.ESTADO_BONO_POR_LLEGAR).count()

    deuda, _ = DeudaPaciente.objects.update_or_create(
        paciente=paciente,
        clinica=clinica,
        defaults={
            'sesiones_sin_pago': sesiones_sin_pago_completo,
            'monto_pendiente': monto_pendiente_total,
            'bonos_por_llegar': bonos_por_llegar,
        },
    )
    return deuda

def editar_pago(pago, monto, medio_pago, estado, folio_bono='', comprobante='', notas=''):
    """Edita un pago existente y recalcula la deuda."""
    with transaction.atomic():
        pago.monto = Decimal(str(monto))
        pago.medio_pago = medio_pago
        pago.estado = estado
        pago.folio_bono = folio_bono
        pago.comprobante = comprobante
        pago.notas = notas
        pago.save(update_fields=['monto', 'medio_pago', 'estado', 'folio_bono', 'comprobante', 'notas'])
        
    recalcular_deuda(pago.paciente, pago.clinica)
    return pago

def eliminar_pago_definitivo(pago, registrado_por):
    """
    Elimina físicamente un pago (Hard Delete).
    Si estaba asociado a un pack, devuelve la sesión al pack.
    """
    with transaction.atomic():
        if pago.medio_pago == RegistroPago.MEDIO_PACK and pago.pack:
            # Bloquear fila para devolución
            pack = PackAtencion.objects.select_for_update().get(id=pago.pack.id)
            if pack.sesiones_usadas > 0:
                pack.sesiones_usadas -= 1
                pack.estado = PackAtencion.ESTADO_ACTIVO
                pack.save(update_fields=['sesiones_usadas', 'estado'])

        paciente = pago.paciente
        clinica = pago.clinica
        pago.delete()

    recalcular_deuda(paciente, clinica)
    return True


def obtener_deuda(paciente, clinica):
    """Retorna el resumen de deuda del paciente, o un objeto neutral si no existe."""
    return DeudaPaciente.objects.filter(paciente=paciente, clinica=clinica).first()


# ────────────────────────────────────────────
# Resumen financiero
# ────────────────────────────────────────────

def obtener_resumen_financiero_paciente(paciente, clinica):
    """Retorna un dict con el resumen financiero completo del paciente."""
    pack_activo = obtener_pack_activo(paciente, clinica)
    deuda = obtener_deuda(paciente, clinica)
    pagos_recientes = (
        RegistroPago.objects.filter(paciente=paciente, clinica=clinica)
        .exclude(estado=RegistroPago.ESTADO_ANULADO)
        .select_related('sesion_kinesica', 'pack')
        .order_by('-fecha_registro')[:10]
    )
    packs_historico = PackAtencion.objects.filter(
        paciente=paciente, clinica=clinica
    ).order_by('-fecha_compra')

    return {
        'pack_activo': pack_activo,
        'deuda': deuda,
        'tiene_deuda': deuda.tiene_deuda if deuda else False,
        'pagos_recientes': pagos_recientes,
        'packs_historico': packs_historico,
    }


def obtener_resumen_financiero_clinica(clinica):
    """Retorna métricas financieras del centro para el dashboard."""
    from django.db.models import Sum, Count
    from datetime import date

    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    pagos_mes = RegistroPago.objects.filter(
        clinica=clinica,
        fecha_registro__date__gte=inicio_mes,
    ).exclude(estado=RegistroPago.ESTADO_ANULADO)

    ingresos_mes = pagos_mes.filter(
        estado=RegistroPago.ESTADO_PAGADO
    ).aggregate(total=Sum('monto'))['total'] or 0

    bonos_pendientes = RegistroPago.objects.filter(
        clinica=clinica,
        estado=RegistroPago.ESTADO_BONO_POR_LLEGAR,
    ).count()

    pacientes_con_deuda = DeudaPaciente.objects.filter(
        clinica=clinica,
        sesiones_sin_pago__gt=0,
    ).count()

    packs_activos = PackAtencion.objects.filter(
        clinica=clinica,
        estado=PackAtencion.ESTADO_ACTIVO,
    ).count()

    return {
        'ingresos_mes': ingresos_mes,
        'bonos_pendientes': bonos_pendientes,
        'pacientes_con_deuda': pacientes_con_deuda,
        'packs_activos': packs_activos,
    }


# ────────────────────────────────────────────
# Configuración
# ────────────────────────────────────────────

def obtener_configuracion(clinica):
    """Retorna la configuración de pagos de la clínica, creando una por defecto si no existe."""
    config, _ = ConfiguracionPagos.objects.get_or_create(clinica=clinica)
    return config
