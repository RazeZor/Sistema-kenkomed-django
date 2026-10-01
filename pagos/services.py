"""
Lógica de negocio del módulo de pagos.
Todas las funciones son puras y no acceden a request directamente.
"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, F, Q, Count

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


def crear_pack(paciente, clinica, nombre, total_sesiones, precio, registrado_por, medio_pago=None, fecha_vencimiento=None, notas='', folio_bono='', comprobante='', estado=RegistroPago.ESTADO_PAGADO, adjunto=None):
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
        if pack.precio_total > 0:
            if medio_pago:
                # Pago inmediato: entra a caja con el estado seleccionado
                RegistroPago.objects.create(
                    paciente=paciente,
                    clinica=clinica,
                    pack=pack,
                    medio_pago=medio_pago,
                    monto=pack.precio_total,
                    estado=estado,
                    folio_bono=folio_bono,
                    comprobante=comprobante,
                    adjunto=adjunto,
                    registrado_por=registrado_por,
                    notas=f'Pago por compra de pack: {pack.nombre}. {notas}'.strip(),
                )
            else:
                # Sin pago inmediato: queda como deuda pendiente del paciente
                RegistroPago.objects.create(
                    paciente=paciente,
                    clinica=clinica,
                    pack=pack,
                    medio_pago=RegistroPago.MEDIO_EFECTIVO,  # medio provisional; se actualizará al pagar
                    monto=pack.precio_total,
                    estado=RegistroPago.ESTADO_PENDIENTE,
                    registrado_por=registrado_por,
                    notas=f'Deuda por pack: {pack.nombre} (pendiente de pago)',
                )
            recalcular_deuda(paciente, clinica)
    return pack


def acumular_sesiones_pack(pack, sesiones_extra, precio_extra, registrado_por, medio_pago=None, notas='', folio_bono='', comprobante='', estado=RegistroPago.ESTADO_PAGADO, adjunto=None):
    """
    Suma sesiones y precio a un pack activo existente en lugar de crear uno nuevo.
    Registra el ingreso (o deuda) correspondiente al aporte adicional.
    """
    with transaction.atomic():
        pack = PackAtencion.objects.select_for_update().get(id=pack.id)
        pack.total_sesiones += int(sesiones_extra)
        pack.precio_total += Decimal(str(precio_extra)) if precio_extra else Decimal('0')
        if notas:
            pack.notas = (pack.notas + f'\n+ {sesiones_extra} sesiones acumuladas. {notas}').strip()
        else:
            pack.notas = (pack.notas + f'\n+ {sesiones_extra} sesiones acumuladas.').strip()
        # Si estaba agotado, reactivar
        if pack.estado == PackAtencion.ESTADO_AGOTADO and pack.sesiones_disponibles > 0:
            pack.estado = PackAtencion.ESTADO_ACTIVO
        pack.save(update_fields=['total_sesiones', 'precio_total', 'notas', 'estado'])

        precio_dec = Decimal(str(precio_extra)) if precio_extra else Decimal('0')
        if precio_dec > 0:
            if medio_pago:
                RegistroPago.objects.create(
                    paciente=pack.paciente,
                    clinica=pack.clinica,
                    pack=pack,
                    medio_pago=medio_pago,
                    monto=precio_dec,
                    estado=estado,
                    folio_bono=folio_bono,
                    comprobante=comprobante,
                    adjunto=adjunto,
                    registrado_por=registrado_por,
                    notas=f'Recarga pack: +{sesiones_extra} sesiones — {pack.nombre}. {notas}'.strip(),
                )
            else:
                RegistroPago.objects.create(
                    paciente=pack.paciente,
                    clinica=pack.clinica,
                    pack=pack,
                    medio_pago=RegistroPago.MEDIO_EFECTIVO,
                    monto=precio_dec,
                    estado=RegistroPago.ESTADO_PENDIENTE,
                    registrado_por=registrado_por,
                    notas=f'Deuda recarga pack: +{sesiones_extra} sesiones — {pack.nombre} (pendiente de pago)',
                )
            recalcular_deuda(pack.paciente, pack.clinica)
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
    medio_pago_2='',
    monto_2=0,
    comprobante_2='',
    adjunto=None,
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
        medio_pago_2=medio_pago_2,
        monto_2=Decimal(str(monto_2)) if monto_2 else Decimal('0'),
        comprobante_2=comprobante_2,
        adjunto=adjunto,
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


def pago_masivo_deuda(
    paciente,
    clinica,
    monto_total,
    medio_pago,
    registrado_por,
    folio_bono='',
    notas='',
    medio_pago_2='',
    monto_2=0,
    comprobante_2='',
    comprobante='',
    monto_1=None,
    adjunto=None,
    estado=RegistroPago.ESTADO_PAGADO,
):
    """Liquida o abona a las sesiones con deuda usando un pago (soporta pago mixto y adjunto)."""
    from SesionesKinesicas.models import SesionKinesica
    
    monto_ingresado = Decimal(str(monto_total))
    if monto_ingresado <= 0:
        return False

    m2 = Decimal(str(monto_2)) if (medio_pago_2 and monto_2) else Decimal('0')
    m1 = Decimal(str(monto_1)) if monto_1 is not None else (monto_ingresado - m2)
        
    with transaction.atomic():
        pagos_activos = RegistroPago.objects.filter(
            paciente=paciente, clinica=clinica
        ).exclude(estado=RegistroPago.ESTADO_ANULADO)
        
        config = obtener_configuracion(clinica)
        precio_default = config.precio_sesion_default
        
        monto_restante = monto_ingresado
        pago_afectado = False
        
        # 1. Intentar saldar pagos explícitos 'Pendientes'
        pagos_pendientes = pagos_activos.filter(
            estado__in=[RegistroPago.ESTADO_PENDIENTE, RegistroPago.ESTADO_BONO_POR_LLEGAR]
        ).order_by('fecha_registro')
        
        for p in pagos_pendientes:
            if monto_restante <= 0:
                break
            p_total = p.monto_total
            costo_base = p_total if p_total > 0 else (precio_default if precio_default > 0 else Decimal('25000'))
            monto_aplicar = min(monto_restante, costo_base)
            
            if monto_aplicar >= p_total and p_total > 0:
                p.estado = estado
                p.medio_pago = medio_pago
                if m2 > 0 and medio_pago_2:
                    p.monto = m1
                    p.medio_pago_2 = medio_pago_2
                    p.monto_2 = m2
                    p.comprobante_2 = comprobante_2
                else:
                    p.monto = monto_aplicar
                    p.medio_pago_2 = ''
                    p.monto_2 = Decimal('0')
                if folio_bono: p.folio_bono = folio_bono
                if comprobante: p.comprobante = comprobante
                if adjunto: p.adjunto = adjunto
                p.fecha_registro = timezone.now()
                p.notas = (p.notas + f" | Saldado. {notas}").strip()
                p.save()
                monto_restante -= p.monto_total
                pago_afectado = True
            else:
                RegistroPago.objects.create(
                    paciente=paciente, clinica=clinica, sesion_kinesica=p.sesion_kinesica,
                    pack=p.pack, medio_pago=medio_pago,
                    monto=m1 if (m2 > 0 and medio_pago_2) else monto_aplicar,
                    medio_pago_2=medio_pago_2 if (m2 > 0 and medio_pago_2) else '',
                    monto_2=m2 if (m2 > 0 and medio_pago_2) else Decimal('0'),
                    comprobante_2=comprobante_2 if (m2 > 0 and medio_pago_2) else '',
                    estado=estado, folio_bono=folio_bono,
                    comprobante=comprobante, adjunto=adjunto,
                    registrado_por=registrado_por, notas=f"Abono parcial a deuda. {notas}".strip()
                )
                p.monto = max(Decimal('0'), p_total - monto_aplicar)
                p.save(update_fields=['monto'])
                monto_restante = Decimal('0')
                pago_afectado = True

        # 2. Buscar sesiones con deuda (huérfanas o sin pago)
        if monto_restante > 0 or not pago_afectado:
            sesiones = SesionKinesica.objects.filter(
                paciente=paciente, ciclo__clinica=clinica
            ).order_by('fecha_creacion')
            
            for sesion in sesiones:
                if monto_restante <= 0:
                    break
                    
                pagos_sesion = pagos_activos.filter(sesion_kinesica=sesion)
                if pagos_sesion.filter(medio_pago=RegistroPago.MEDIO_PACK).exists():
                    continue
                    
                pagado = pagos_sesion.filter(estado__in=[RegistroPago.ESTADO_PAGADO, RegistroPago.ESTADO_BONO_POR_LLEGAR]).aggregate(total=Sum(F('monto') + F('monto_2')))['total'] or Decimal('0')
                costo_ref = precio_default if precio_default > 0 else Decimal('25000')
                deuda_sesion = costo_ref - pagado
                
                if deuda_sesion > 0:
                    monto_aplicar = min(monto_restante, deuda_sesion)
                    RegistroPago.objects.create(
                        paciente=paciente, clinica=clinica, sesion_kinesica=sesion,
                        medio_pago=medio_pago,
                        monto=m1 if (m2 > 0 and medio_pago_2) else monto_aplicar,
                        medio_pago_2=medio_pago_2 if (m2 > 0 and medio_pago_2) else '',
                        monto_2=m2 if (m2 > 0 and medio_pago_2) else Decimal('0'),
                        comprobante_2=comprobante_2 if (m2 > 0 and medio_pago_2) else '',
                        estado=estado, folio_bono=folio_bono,
                        comprobante=comprobante, adjunto=adjunto,
                        registrado_por=registrado_por, notas=f"Pago deuda sesión #{sesion.numero_sesion}. {notas}".strip()
                    )
                    monto_restante -= (monto_aplicar if not (m2 > 0 and medio_pago_2) else (m1 + m2))
                    pago_afectado = True
                    
        # 3. Si no había deuda específica o sobró saldo (Abono Libre a favor del paciente)
        if monto_restante > 0 or not pago_afectado:
            monto_final = m1 if (m2 > 0 and medio_pago_2) else (monto_restante if monto_restante > 0 else monto_ingresado)
            RegistroPago.objects.create(
                paciente=paciente, clinica=clinica, sesion_kinesica=None,
                medio_pago=medio_pago,
                monto=monto_final,
                medio_pago_2=medio_pago_2 if (m2 > 0 and medio_pago_2) else '',
                monto_2=m2 if (m2 > 0 and medio_pago_2) else Decimal('0'),
                comprobante_2=comprobante_2 if (m2 > 0 and medio_pago_2) else '',
                estado=estado, folio_bono=folio_bono,
                comprobante=comprobante, adjunto=adjunto,
                registrado_por=registrado_por, notas=f"Abono a deuda. {notas}".strip()
            )
            
    recalcular_deuda(paciente, clinica)
    return True


# ────────────────────────────────────────────
# Deuda
# ────────────────────────────────────────────

def recalcular_deuda(paciente, clinica):
    """
    Recalcula el resumen de deuda del paciente evaluando micromorososidades por sesión.
    Los pagos asociados a una sesión cubren únicamente dicha sesión y no se consideran
    abonos libres para descontar deudas de otras sesiones o packs.
    Suma tanto el monto principal como el monto del segundo medio (monto_2).
    """
    from SesionesKinesicas.models import SesionKinesica

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
    costo_referencia = precio_default if precio_default > 0 else Decimal('25000')

    # 1. Abonos Libres (Pagos sin sesión y sin pack confirmados a favor del paciente)
    abonos_libres = pagos_activos.filter(
        sesion_kinesica__isnull=True,
        pack__isnull=True,
        estado=RegistroPago.ESTADO_PAGADO
    ).aggregate(total=Sum(F('monto') + F('monto_2')))['total'] or Decimal('0')

    # 2. Deuda explícita sin sesión (Registros manuales pendientes + deudas de packs sin pago)
    deuda_explicita_sin_sesion = pagos_activos.filter(
        sesion_kinesica__isnull=True,
        estado__in=[RegistroPago.ESTADO_PENDIENTE, RegistroPago.ESTADO_BONO_POR_LLEGAR]
    ).aggregate(total=Sum(F('monto') + F('monto_2')))['total'] or Decimal('0')

    # 3. Calcular deuda sesión por sesión
    monto_pendiente_sesiones = Decimal('0')
    sesiones_sin_pago_completo = 0

    for sesion in total_sesiones:
        pagos_sesion = pagos_activos.filter(sesion_kinesica=sesion)
        
        # Si fue pagada con pack, la sesión está completamente cubierta
        if pagos_sesion.filter(medio_pago=RegistroPago.MEDIO_PACK).exists():
            continue
            
        pagado_a_sesion = pagos_sesion.filter(
            estado__in=[RegistroPago.ESTADO_PAGADO, RegistroPago.ESTADO_BONO_POR_LLEGAR]
        ).aggregate(total=Sum(F('monto') + F('monto_2')))['total'] or Decimal('0')
        
        if pagado_a_sesion > 0:
            # La sesión fue pagada directamente. NO tiene deuda.
            # Su pago pertenece a esta sesión y NUNCA se descuenta de la deuda de otras sesiones ni packs.
            continue

        # Si no tiene pago confirmado, verificar si tiene un registro de pago pendiente explícito
        pago_pendiente = pagos_sesion.filter(estado=RegistroPago.ESTADO_PENDIENTE).first()
        if pago_pendiente and (pago_pendiente.monto + pago_pendiente.monto_2) > 0:
            monto_pendiente_sesiones += (pago_pendiente.monto + pago_pendiente.monto_2)
            sesiones_sin_pago_completo += 1
        else:
            # Sesión sin ningún pago asociado
            monto_pendiente_sesiones += costo_referencia
            sesiones_sin_pago_completo += 1

    # 4. Cálculo final: solo los abonos explícitamente libres disminuyen la deuda
    monto_pendiente_total = monto_pendiente_sesiones + deuda_explicita_sin_sesion - abonos_libres
    if monto_pendiente_total < Decimal('0'):
        monto_pendiente_total = Decimal('0')
    
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

def editar_pago(pago, monto, medio_pago, estado, folio_bono='', comprobante='', notas='', medio_pago_2='', monto_2=0, comprobante_2='', adjunto=None):
    """Edita un pago existente y recalcula la deuda."""
    with transaction.atomic():
        pago.monto = Decimal(str(monto))
        pago.medio_pago = medio_pago
        pago.estado = estado
        pago.folio_bono = folio_bono
        pago.comprobante = comprobante
        pago.notas = notas
        pago.medio_pago_2 = medio_pago_2
        pago.monto_2 = Decimal(str(monto_2)) if monto_2 else Decimal('0')
        pago.comprobante_2 = comprobante_2
        if adjunto:
            pago.adjunto = adjunto
        pago.save()
        
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
    ).aggregate(total=Sum(F('monto') + F('monto_2')))['total'] or 0

    bonos_pendientes = RegistroPago.objects.filter(
        clinica=clinica,
        estado=RegistroPago.ESTADO_BONO_POR_LLEGAR,
    ).count()

    from django.db.models import Q
    pacientes_con_deuda = DeudaPaciente.objects.filter(
        clinica=clinica,
    ).filter(
        Q(sesiones_sin_pago__gt=0) | Q(monto_pendiente__gt=0)
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
