from django.db import models


class Plan(models.Model):
    TIPO_INDIVIDUAL = 'individual'
    TIPO_PRO = 'clinico_pro'
    TIPO_CLINICA = 'clinica'
    TIPO_LEGACY = 'legacy_full'

    PLAN_CHOICES = [
        (TIPO_INDIVIDUAL, 'Individual'),
        (TIPO_PRO, 'Clínico Pro'),
        (TIPO_CLINICA, 'Clínica / Centro'),
        (TIPO_LEGACY, 'Legacy Full Access'),
    ]

    codigo = models.CharField(max_length=30, choices=PLAN_CHOICES, unique=True, verbose_name="Código del Plan")
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Plan")
    max_kinesiologos = models.PositiveIntegerField(default=1, verbose_name="Máximo Kinesiólogos")
    max_pacientes_activos = models.IntegerField(default=100, help_text="-1 para ilimitados", verbose_name="Máximo Pacientes Activos")

    # Feature Flags / Capacidades del Plan
    permite_qr_anamnesis = models.BooleanField(default=False, verbose_name="Anamnesis Remota (QR)")
    permite_recetas_digitales = models.BooleanField(default=False, verbose_name="Recetas Médicas Digitales")
    permite_reportes_dss = models.BooleanField(default=False, verbose_name="Reportes DSS & Analítica")
    permite_exportacion_arco = models.BooleanField(default=False, verbose_name="Exportación ARCO (JSON/HTML)")
    permite_auditoria_pdf = models.BooleanField(default=False, verbose_name="Exportación Auditoría PDF")
    permite_multi_seda = models.BooleanField(default=False, verbose_name="Multi-Seda / Migración Pacientes")
    permite_roles_avanzados = models.BooleanField(default=False, verbose_name="Roles Avanzados (Secretaría/Admin)")
    permite_logo_personalizado = models.BooleanField(default=False, verbose_name="Logo Personalizado en Informes")
    permite_dashboard_gerencial = models.BooleanField(default=False, verbose_name="Dashboard Gerencial & Métricas")
    permite_gestion_pagos = models.BooleanField(default=True, verbose_name="Gestión de Pagos & Packs de Atención")

    class Meta:
        verbose_name = "Plan de Suscripción"
        verbose_name_plural = "Planes de Suscripción"
        ordering = ['id']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"


class SuscripcionClinica(models.Model):
    ESTADO_ACTIVA = 'activa'
    ESTADO_CANCELADA = 'cancelada'
    ESTADO_PRUEBA = 'prueba'

    ESTADOS_CHOICES = [
        (ESTADO_ACTIVA, 'Activa'),
        (ESTADO_CANCELADA, 'Cancelada'),
        (ESTADO_PRUEBA, 'Prueba Gratuita'),
    ]

    clinica = models.OneToOneField('clinicas.Clinica', on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='suscripciones')
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default=ESTADO_ACTIVA)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    es_legacy = models.BooleanField(default=False, help_text="Aplica para cuentas iniciales de producción con acceso completo")

    class Meta:
        verbose_name = "Suscripción de Clínica"
        verbose_name_plural = "Suscripciones de Clínicas"

    def __str__(self):
        legacy_str = " [LEGACY]" if self.es_legacy else ""
        return f"{self.clinica.nombre} - Plan {self.plan.nombre}{legacy_str}"

    def tiene_feature(self, feature_name):
        """Devuelve True si la cuenta es legacy o si el plan actual habilita la característica."""
        if self.es_legacy:
            return True
        if self.estado != self.ESTADO_ACTIVA and self.estado != self.ESTADO_PRUEBA:
            return False
        if not self.plan:
            return False
        return getattr(self.plan, feature_name, False)
