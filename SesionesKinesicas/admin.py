from django.contrib import admin
from .models import SesionKinesica


@admin.register(SesionKinesica)
class SesionKinesicaAdmin(admin.ModelAdmin):
    list_display = (
        'numero_sesion', 
        'paciente', 
        'clinico', 
        'es_primera_sesion',
        'fecha_creacion'
    )
    list_filter = ('es_primera_sesion', 'fecha_creacion', 'clinico')
    search_fields = ('paciente__nombre', 'paciente__apellido', 'paciente__rut')
    readonly_fields = ('fecha_creacion', 'fecha_ultima_actualizacion', 'numero_sesion')
    
    fieldsets = (
        ('Información de la Sesión', {
            'fields': ('paciente', 'clinico', 'numero_sesion', 'es_primera_sesion')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_ultima_actualizacion')
        }),
        ('Evaluación Inicial (1ra Sesión)', {
            'fields': ('evaluacion_inicial',),
            'classes': ('collapse',)
        }),
        ('Contenido Clínico', {
            'fields': ('notas_clinicas', 'evolucion')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Si es una edición
            readonly.append('es_primera_sesion')  # No permitir cambiar esto después de crear
        return readonly
