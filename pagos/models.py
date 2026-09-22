from django.db import models


class PackAtencion(models.Model):
    """Pack de sesiones vendido a un paciente (ej: 'Pack 10 sesiones')."""

    ESTADO_ACTIVO = 'activo'
    ESTADO_AGOTADO = 'agotado'
    ESTADO_VENCIDO = 'vencido'
    ESTADO_CANCELADO = 'cancelado'
    ESTADOS = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_AGOTADO, 'Agotado'),
        (ESTADO_VENCIDO, 'Vencido'),
        (ESTADO_CANCELADO, 'Cancelado'),
    ]

    paciente = models.ForeignKey(
        'Login.Paciente',
        on_delete=models.CASCADE,
        related_name='packs_atencion',
        verbose_name='Paciente',
    )
    clinica = models.ForeignKey(
        'clinicas.Clinica',
        on_delete=models.CASCADE,
        related_name='packs_atencion',
        verbose_name='Clínica',
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del pack',
        help_text='Ej: Pack 10 sesiones, Pack mensual',
    )
    total_sesiones = models.PositiveIntegerField(
        verbose_name='Total de sesiones incluidas',
    )
    sesiones_usadas = models.PositiveIntegerField(
        default=0,
        verbose_name='Sesiones consumidas',
    )
    precio_total = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Precio total del pack ($)',
    )
    fecha_compra = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de compra',
    )
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de vencimiento',
        help_text='Opcional. Si vence, las sesiones restantes quedan expiradas.',
    )
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default=ESTADO_ACTIVO,
        verbose_name='Estado',
    )
    registrado_por = models.ForeignKey(
        'Login.Clinico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packs_registrados',
        verbose_name='Registrado por',
    )
    notas = models.TextField(blank=True, default='', verbose_name='Notas')

    class Meta:
        verbose_name = 'Pack de Atención'
        verbose_name_plural = 'Packs de Atención'
        ordering = ['-fecha_compra']
        indexes = [
            models.Index(fields=['paciente', 'estado']),
            models.Index(fields=['clinica', '-fecha_compra']),
        ]

    def __str__(self):
        return (
            f'{self.nombre} — {self.paciente.nombre} {self.paciente.apellido} '
            f'({self.sesiones_usadas}/{self.total_sesiones})'
        )

    @property
    def sesiones_disponibles(self):
        return max(0, self.total_sesiones - self.sesiones_usadas)

    @property
    def esta_activo(self):
        return self.estado == self.ESTADO_ACTIVO and self.sesiones_disponibles > 0

    @property
    def porcentaje_uso(self):
        if self.total_sesiones == 0:
            return 0
        return round((self.sesiones_usadas / self.total_sesiones) * 100)


class RegistroPago(models.Model):
    """Registro de un pago individual por sesión o abono al pack."""

    MEDIO_BONO_FONASA = 'bono_fonasa'
    MEDIO_BONO_ISAPRE = 'bono_isapre'
    MEDIO_EFECTIVO = 'particular_efectivo'
    MEDIO_TRANSFERENCIA = 'transferencia'
    MEDIO_TARJETA = 'tarjeta'
    MEDIO_CONVENIO = 'convenio'
    MEDIO_PACK = 'pack'

    MEDIOS_PAGO = [
        (MEDIO_BONO_FONASA, 'Bono Fonasa'),
        (MEDIO_BONO_ISAPRE, 'Bono Isapre'),
        (MEDIO_EFECTIVO, 'Efectivo'),
        (MEDIO_TRANSFERENCIA, 'Transferencia'),
        (MEDIO_TARJETA, 'Tarjeta Débito/Crédito'),
        (MEDIO_CONVENIO, 'Convenio / Cortesía'),
        (MEDIO_PACK, 'Descontado del Pack'),
    ]

    ESTADO_PAGADO = 'pagado'
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_BONO_POR_LLEGAR = 'bono_por_llegar'
    ESTADO_ANULADO = 'anulado'

    ESTADOS = [
        (ESTADO_PAGADO, 'Pagado'),
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_BONO_POR_LLEGAR, 'Bono por llegar'),
        (ESTADO_ANULADO, 'Anulado'),
    ]

    paciente = models.ForeignKey(
        'Login.Paciente',
        on_delete=models.CASCADE,
        related_name='registros_pago',
        verbose_name='Paciente',
    )
    clinica = models.ForeignKey(
        'clinicas.Clinica',
        on_delete=models.CASCADE,
        related_name='registros_pago',
        verbose_name='Clínica',
    )
    sesion_kinesica = models.ForeignKey(
        'SesionesKinesicas.SesionKinesica',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registros_pago',
        verbose_name='Sesión kinésica asociada',
    )
    pack = models.ForeignKey(
        PackAtencion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_descontados',
        verbose_name='Pack asociado',
    )
    medio_pago = models.CharField(
        max_length=30,
        choices=MEDIOS_PAGO,
        verbose_name='Medio de pago',
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Monto ($)',
    )
    folio_bono = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name='Folio / N° bono',
        help_text='Número de folio del bono Fonasa o Isapre',
    )
    comprobante = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Referencia / Comprobante',
        help_text='N° de transferencia, voucher, etc.',
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PAGADO,
        verbose_name='Estado del pago',
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de registro',
    )
    registrado_por = models.ForeignKey(
        'Login.Clinico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_registrados',
        verbose_name='Registrado por',
    )
    notas = models.TextField(blank=True, default='', verbose_name='Notas')

    class Meta:
        verbose_name = 'Registro de Pago'
        verbose_name_plural = 'Registros de Pago'
        ordering = ['-fecha_registro']
        indexes = [
            models.Index(fields=['paciente', '-fecha_registro']),
            models.Index(fields=['clinica', '-fecha_registro']),
            models.Index(fields=['sesion_kinesica']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return (
            f'{self.get_medio_pago_display()} — '
            f'{self.paciente.nombre} {self.paciente.apellido} — '
            f'${self.monto} ({self.get_estado_display()})'
        )

    @property
    def es_bono(self):
        return self.medio_pago in (self.MEDIO_BONO_FONASA, self.MEDIO_BONO_ISAPRE)

    @property
    def tiene_pendiente(self):
        return self.estado in (self.ESTADO_PENDIENTE, self.ESTADO_BONO_POR_LLEGAR)


class DeudaPaciente(models.Model):
    """
    Resumen de deuda por paciente-clínica.
    Se recalcula cada vez que se registra o modifica un pago.
    """

    paciente = models.ForeignKey(
        'Login.Paciente',
        on_delete=models.CASCADE,
        related_name='deuda_resumen',
        verbose_name='Paciente',
    )
    clinica = models.ForeignKey(
        'clinicas.Clinica',
        on_delete=models.CASCADE,
        related_name='deudas_pacientes',
        verbose_name='Clínica',
    )
    sesiones_sin_pago = models.PositiveIntegerField(
        default=0,
        verbose_name='Sesiones sin pago',
    )
    monto_pendiente = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Monto pendiente ($)',
    )
    bonos_por_llegar = models.PositiveIntegerField(
        default=0,
        verbose_name='Bonos por recibir',
    )
    ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización',
    )

    class Meta:
        verbose_name = 'Deuda de Paciente'
        verbose_name_plural = 'Deudas de Pacientes'
        unique_together = ('paciente', 'clinica')
        indexes = [
            models.Index(fields=['clinica', 'sesiones_sin_pago']),
        ]

    def __str__(self):
        return (
            f'{self.paciente.nombre} {self.paciente.apellido} — '
            f'${self.monto_pendiente} pendiente'
        )

    @property
    def tiene_deuda(self):
        return self.sesiones_sin_pago > 0 or self.monto_pendiente > 0

    @property
    def tiene_bonos_pendientes(self):
        return self.bonos_por_llegar > 0


class ConfiguracionPagos(models.Model):
    """Configuración del módulo de pagos por clínica."""

    clinica = models.OneToOneField(
        'clinicas.Clinica',
        on_delete=models.CASCADE,
        related_name='configuracion_pagos',
        verbose_name='Clínica',
    )
    precio_sesion_default = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name='Precio default por sesión ($)',
        help_text='Se autocompleta al registrar pagos individuales.',
    )
    alerta_deuda_activa = models.BooleanField(
        default=True,
        verbose_name='Mostrar alerta de deuda en ficha',
    )
    dias_tolerancia_bono = models.PositiveIntegerField(
        default=7,
        verbose_name='Días de tolerancia para entrega de bono',
        help_text='Si el bono no llega en este plazo, se marca como deuda.',
    )

    class Meta:
        verbose_name = 'Configuración de Pagos'
        verbose_name_plural = 'Configuraciones de Pagos'

    def __str__(self):
        return f'Configuración pagos — {self.clinica.nombre}'
