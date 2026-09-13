from django.contrib import admin
from .models import EvaluacionOswestry, EvaluacionLEFS, EvaluacionQuickDASH, EvaluacionWOMAC, EvaluacionTUG, EvaluacionBerg, EvaluacionTinetti

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


@admin.register(EvaluacionQuickDASH)
class EvaluacionQuickDASHAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'get_porcentaje_discapacidad')
    search_fields = ('paciente__nombre', 'paciente__rut')


@admin.register(EvaluacionWOMAC)
class EvaluacionWOMACAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'get_total_puntos')
    search_fields = ('paciente__nombre', 'paciente__rut')


@admin.register(EvaluacionTUG)
class EvaluacionTUGAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'tiempo_segundos', 'usa_ayuda_marcha', 'get_nivel_riesgo')
    list_filter = ('fecha_evaluacion', 'clinico', 'usa_ayuda_marcha')
    search_fields = ('paciente__nombre', 'paciente__rut', 'clinico__nombre')
    readonly_fields = ('fecha_evaluacion', 'get_interpretacion_display')

    fieldsets = (
        ('Información General', {
            'fields': ('paciente', 'ciclo', 'clinico', 'fecha_evaluacion')
        }),
        ('Resultado del Test', {
            'fields': ('tiempo_segundos', 'usa_ayuda_marcha', 'observaciones', 'get_interpretacion_display')
        }),
        ('Notas Clínicas', {
            'fields': ('notas_clinicas',)
        }),
    )

    def get_nivel_riesgo(self, obj):
        return obj.get_interpretacion()['nivel']
    get_nivel_riesgo.short_description = 'Nivel de Riesgo'

    def get_interpretacion_display(self, obj):
        interp = obj.get_interpretacion()
        return f"{interp['nivel']} ({interp['rango']}): {interp['descripcion']}"
    get_interpretacion_display.short_description = 'Interpretación Completa'


@admin.register(EvaluacionBerg)
class EvaluacionBergAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'get_total_puntos', 'get_nivel_riesgo')
    list_filter = ('fecha_evaluacion', 'clinico')
    search_fields = ('paciente__nombre', 'paciente__rut', 'clinico__nombre')
    readonly_fields = ('fecha_evaluacion', 'get_interpretacion_display')

    fieldsets = (
        ('Información General', {
            'fields': ('paciente', 'ciclo', 'clinico', 'fecha_evaluacion')
        }),
        ('Ítems del Test (14 Tareas)', {
            'fields': (
                'item_01', 'item_02', 'item_03', 'item_04', 'item_05',
                'item_06', 'item_07', 'item_08', 'item_09', 'item_10',
                'item_11', 'item_12', 'item_13', 'item_14',
            )
        }),
        ('Interpretación y Notas', {
            'fields': ('get_interpretacion_display', 'notas_clinicas')
        }),
    )

    def get_nivel_riesgo(self, obj):
        return obj.get_interpretacion()['nivel']
    get_nivel_riesgo.short_description = 'Nivel de Riesgo'

    def get_interpretacion_display(self, obj):
        interp = obj.get_interpretacion()
        return f"{interp['nivel']} ({interp['total']}/56 pts) — Grupo: {interp['grupo_funcional']}"
    get_interpretacion_display.short_description = 'Interpretación Completa'


@admin.register(EvaluacionTinetti)
class EvaluacionTinettiAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'clinico', 'fecha_evaluacion', 'get_total_puntos', 'get_puntaje_equilibrio', 'get_puntaje_marcha', 'get_nivel_riesgo')
    list_filter = ('fecha_evaluacion', 'clinico')
    search_fields = ('paciente__nombre', 'paciente__rut', 'clinico__nombre')
    readonly_fields = ('fecha_evaluacion', 'get_interpretacion_display')

    fieldsets = (
        ('Información General', {
            'fields': ('paciente', 'ciclo', 'clinico', 'fecha_evaluacion')
        }),
        ('Subescala Equilibrio (9 ítems)', {
            'fields': (
                'eq_01_sentado', 'eq_02_levantarse', 'eq_03_intentos',
                'eq_04_equi_inmediato', 'eq_05_equi_bipedestacion',
                'eq_06_empujon', 'eq_07_ojos_cerrados', 'eq_08_giro_360',
                'eq_09_sentarse',
            )
        }),
        ('Subescala Marcha (7 ítems)', {
            'fields': (
                'ma_01_iniciacion', 'ma_02_longitud_altura', 'ma_03_simetria',
                'ma_04_continuidad', 'ma_05_trayectoria', 'ma_06_tronco',
                'ma_07_postura_marcha',
            )
        }),
        ('Interpretación y Notas', {
            'fields': ('get_interpretacion_display', 'notas_clinicas')
        }),
    )

    def get_nivel_riesgo(self, obj):
        return obj.get_interpretacion()['nivel']
    get_nivel_riesgo.short_description = 'Nivel de Riesgo'

    def get_interpretacion_display(self, obj):
        interp = obj.get_interpretacion()
        return f"{interp['nivel']} ({interp['total']}/28 pts: Eq {interp['equilibrio']}/16, Ma {interp['marcha']}/12)"
    get_interpretacion_display.short_description = 'Interpretación Completa'

