from django.contrib import admin
from .models import Plan, SuscripcionClinica


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'max_kinesiologos', 'max_pacientes_activos', 'permite_recetas_digitales', 'permite_qr_anamnesis', 'permite_auditoria_pdf')
    list_filter = ('codigo',)
    search_fields = ('nombre', 'codigo')


@admin.register(SuscripcionClinica)
class SuscripcionClinicaAdmin(admin.ModelAdmin):
    list_display = ('clinica', 'plan', 'estado', 'override_max_adjuntos', 'es_legacy', 'fecha_inicio', 'fecha_vencimiento')
    list_editable = ('override_max_adjuntos',)
    list_filter = ('estado', 'es_legacy', 'plan')
    search_fields = ('clinica__nombre', 'clinica__rut_empresa')

