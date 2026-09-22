from django.contrib import admin
from .models import PackAtencion, RegistroPago, DeudaPaciente, ConfiguracionPagos


@admin.register(PackAtencion)
class PackAtencionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'paciente', 'clinica', 'total_sesiones', 'sesiones_usadas', 'estado', 'fecha_compra']
    list_filter = ['estado', 'clinica']
    search_fields = ['paciente__nombre', 'paciente__apellido', 'nombre']
    readonly_fields = ['fecha_compra', 'sesiones_usadas']
    date_hierarchy = 'fecha_compra'


@admin.register(RegistroPago)
class RegistroPagoAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'clinica', 'medio_pago', 'monto', 'estado', 'fecha_registro', 'registrado_por']
    list_filter = ['medio_pago', 'estado', 'clinica']
    search_fields = ['paciente__nombre', 'paciente__apellido', 'folio_bono', 'comprobante']
    readonly_fields = ['fecha_registro']
    date_hierarchy = 'fecha_registro'


@admin.register(DeudaPaciente)
class DeudaPacienteAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'clinica', 'sesiones_sin_pago', 'monto_pendiente', 'bonos_por_llegar', 'ultima_actualizacion']
    list_filter = ['clinica']
    search_fields = ['paciente__nombre', 'paciente__apellido']
    readonly_fields = ['ultima_actualizacion']


@admin.register(ConfiguracionPagos)
class ConfiguracionPagosAdmin(admin.ModelAdmin):
    list_display = ['clinica', 'precio_sesion_default', 'alerta_deuda_activa', 'dias_tolerancia_bono']
