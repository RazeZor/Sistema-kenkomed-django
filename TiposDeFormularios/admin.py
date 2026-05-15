from django.contrib import admin
from .models import EvaluacionOswestry

@admin.register(EvaluacionOswestry)
class EvaluacionOswestryAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'get_porcentaje_incapacidad', 'get_nivel_incapacidad')
    list_filter = ('fecha_evaluacion', 'clinico')
    search_fields = ('paciente__nombre', 'paciente__rut', 'clinico__nombre')
    readonly_fields = ('fecha_evaluacion', 'get_total_puntos', 'get_porcentaje_incapacidad', 'get_interpretacion_display')
    
    fieldsets = (
        ('Información General', {
            'fields': ('paciente', 'clinico', 'fecha_evaluacion')
        }),
        ('Secciones del Cuestionario', {
            'fields': (
                'seccion_1_intensidad_dolor',
                'seccion_2_estar_de_pie',
                'seccion_3_cuidados_personales',
                'seccion_4_dormir',
                'seccion_5_levantar_peso',
                'seccion_6_actividad_sexual',
                'seccion_7_andar',
                'seccion_8_vida_social',
                'seccion_9_estar_sentado',
                'seccion_10_viajar',
            )
        }),
        ('Resultados', {
            'fields': ('get_total_puntos', 'get_porcentaje_incapacidad', 'get_interpretacion_display')
        }),
        ('Notas Clínicas', {
            'fields': ('notas_clinicas',)
        }),
    )
    
    def get_nivel_incapacidad(self, obj):
        return obj.get_interpretacion()['nivel']
    get_nivel_incapacidad.short_description = 'Nivel de Incapacidad'
    
    def get_interpretacion_display(self, obj):
        interp = obj.get_interpretacion()
        return f"{interp['nivel']} ({interp['rango']}): {interp['descripcion']}"
    get_interpretacion_display.short_description = 'Interpretación Completa'
