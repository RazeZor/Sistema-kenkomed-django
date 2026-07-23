from django.contrib import admin

from ciclos_clinicos.models import CicloClinico


@admin.register(CicloClinico)
class CicloClinicoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'numero_ciclo', 'paciente', 'clinica', 'estado',
        'clinico_responsable', 'fecha_inicio', 'fecha_cierre',
    )
    list_filter = ('estado', 'clinica')
    search_fields = ('paciente__rut', 'paciente__nombre', 'paciente__apellido')
    readonly_fields = ('fecha_inicio',)
