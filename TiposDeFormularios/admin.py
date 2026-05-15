from django.contrib import admin
from .models import EvaluacionOswestry, EvaluacionLEFS

@admin.register(EvaluacionLEFS)
class EvaluacionLEFSAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'get_total_puntos', 'get_porcentaje_funcionalidad', 'get_nivel_funcionalidad')
    list_filter = ('fecha_evaluacion', 'clinico')
    search_fields = ('paciente__nombre', 'paciente__rut', 'clinico__nombre')
    readonly_fields = ('fecha_evaluacion', 'get_total_puntos', 'get_porcentaje_funcionalidad', 'get_interpretacion_display')
    
    fieldsets = (
        ('Información General', {
            'fields': ('paciente', 'clinico', 'fecha_evaluacion')
        }),
        ('Actividades del Cuestionario', {
            'fields': (
                'actividad_1_trabajo', 'actividad_2_pasatiempos', 'actividad_3_banio',
                'actividad_4_andar_cuartos', 'actividad_5_zapatos', 'actividad_6_cuclillas',
                'actividad_7_levantar_objeto', 'actividad_8_actividades_ligeras',
                'actividad_9_actividades_pesadas', 'actividad_10_coche',
                'actividad_11_caminar_2cuadras', 'actividad_12_caminar_milla',
                'actividad_13_escalones', 'actividad_14_estar_pie', 'actividad_15_estar_sentado',
                'actividad_16_correr_plano', 'actividad_17_correr_desigual',
                'actividad_18_vueltas_bruscas', 'actividad_19_saltar', 'actividad_20_vuelta_cama',
            )
        }),
        ('Resultados', {
            'fields': ('get_total_puntos', 'get_porcentaje_funcionalidad', 'get_interpretacion_display')
        }),
        ('Notas Clínicas', {
            'fields': ('notas_clinicas',)
        }),
    )
    
    def get_nivel_funcionalidad(self, obj):
        return obj.get_interpretacion()['nivel']
    get_nivel_funcionalidad.short_description = 'Nivel de Funcionalidad'
    
    def get_interpretacion_display(self, obj):
        interp = obj.get_interpretacion()
        return f"{interp['nivel']} ({interp['rango']}): {interp['descripcion']}"
    get_interpretacion_display.short_description = 'Interpretación Completa'

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
