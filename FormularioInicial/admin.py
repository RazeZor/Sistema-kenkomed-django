from django.contrib import admin

from .models import ConsentimientoDatos, TokenFormulario


@admin.register(TokenFormulario)
class TokenFormularioAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'clinico', 'activo', 'usado', 'fecha_creacion', 'fecha_expiracion')
    list_filter = ('activo', 'usado')
    search_fields = ('paciente__rut', 'paciente__nombre', 'clinico__rut')
    readonly_fields = ('id', 'fecha_creacion')


@admin.register(ConsentimientoDatos)
class ConsentimientoDatosAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinica', 'origen', 'fecha', 'ip_address')
    list_filter = ('origen', 'clinica')
    search_fields = ('paciente__rut', 'paciente__nombre', 'paciente__apellido')
    readonly_fields = ('fecha',)
