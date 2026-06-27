from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class EvaluacionLEFS(models.Model):
    """
    Escala Funcional de la Extremidad Inferior (LEFS)
    20 actividades, cada una puntúa de 0-4
    Resultado: suma total (rango 0-80)
    Mayor puntaje = mejor función
    """
    
    paciente = models.ForeignKey('Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_lefs')
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_lefs')
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    # 20 actividades del cuestionario (0-4 cada una)
    actividad_1_trabajo = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Trabajo usual, domestico o escuela"
    )
    actividad_2_pasatiempos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Pasatiempos, recreación o deportes"
    )
    actividad_3_banio = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Entrar o salir del baño"
    )
    actividad_4_andar_cuartos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Andar entre cuartos"
    )
    actividad_5_zapatos = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Ponerse zapatos o calcetines"
    )
    actividad_6_cuclillas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Ponerse en cuclillas"
    )
    actividad_7_levantar_objeto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Levantar objeto del piso"
    )
    actividad_8_actividades_ligeras = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Actividades ligeras domesticas"
    )
    actividad_9_actividades_pesadas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Actividades pesadas domesticas"
    )
    actividad_10_coche = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Entrar o salir de un coche"
    )
    actividad_11_caminar_2cuadras = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Caminar 2 cuadras"
    )
    actividad_12_caminar_milla = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Caminar una milla"
    )
    actividad_13_escalones = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Subir o bajar 10 escalones"
    )
    actividad_14_estar_pie = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Estar de pie por 1 hora"
    )
    actividad_15_estar_sentado = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Estar sentado por 1 hora"
    )
    actividad_16_correr_plano = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Correr sobre suelo plano"
    )
    actividad_17_correr_desigual = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Correr sobre suelo desigual"
    )
    actividad_18_vueltas_bruscas = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Hacer vueltas bruscas corriendo"
    )
    actividad_19_saltar = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Saltar"
    )
    actividad_20_vuelta_cama = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="0-4: Darse la vuelta en la cama"
    )
    
    # Notas opcionales
    notas_clinicas = models.TextField(null=True, blank=True, help_text="Observaciones clínicas adicionales")
    
    class Meta:
        verbose_name = "Evaluación LEFS"
        verbose_name_plural = "Evaluaciones LEFS"
        ordering = ['-fecha_evaluacion']
    
    def __str__(self):
        return f"LEFS - {self.paciente.nombre} ({self.fecha_evaluacion.strftime('%d/%m/%Y')})"
    
    def get_total_puntos(self):
        """Calcula la suma total de las 20 actividades"""
        total = (
            self.actividad_1_trabajo + self.actividad_2_pasatiempos +
            self.actividad_3_banio + self.actividad_4_andar_cuartos +
            self.actividad_5_zapatos + self.actividad_6_cuclillas +
            self.actividad_7_levantar_objeto + self.actividad_8_actividades_ligeras +
            self.actividad_9_actividades_pesadas + self.actividad_10_coche +
            self.actividad_11_caminar_2cuadras + self.actividad_12_caminar_milla +
            self.actividad_13_escalones + self.actividad_14_estar_pie +
            self.actividad_15_estar_sentado + self.actividad_16_correr_plano +
            self.actividad_17_correr_desigual + self.actividad_18_vueltas_bruscas +
            self.actividad_19_saltar + self.actividad_20_vuelta_cama
        )
        return total
    
    def get_porcentaje_funcionalidad(self):
        """Calcula el porcentaje de funcionalidad (total/80 * 100)"""
        return round((self.get_total_puntos() / 80) * 100, 1)
    
    def get_interpretacion(self):
        """Devuelve la interpretación clínica según el puntaje"""
        total = self.get_total_puntos()
        
        if total >= 72:  # 90-100%
            return {
                'nivel': 'Funcionalidad Excelente',
                'rango': '72-80 puntos',
                'descripcion': 'Mínima o ninguna limitación funcional. Paciente altamente funcional.',
                'recomendacion': 'Mantener nivel de actividad. Prevención de lesiones.'
            }
        elif total >= 64:  # 80-89%
            return {
                'nivel': 'Funcionalidad Buena',
                'rango': '64-71 puntos',
                'descripcion': 'Limitaciones funcionales leves. Buen nivel de independencia.',
                'recomendacion': 'Continuar rehabilitación. Enfoque en actividades específicas.'
            }
        elif total >= 48:  # 60-79%
            return {
                'nivel': 'Funcionalidad Moderada',
                'rango': '48-63 puntos',
                'descripcion': 'Limitaciones funcionales moderadas. Afecta actividades diarias.',
                'recomendacion': 'Intensificar tratamiento. Terapia funcional dirigida.'
            }
        elif total >= 32:  # 40-59%
            return {
                'nivel': 'Funcionalidad Limitada',
                'rango': '32-47 puntos',
                'descripcion': 'Limitaciones funcionales significativas. Dependencia parcial.',
                'recomendacion': 'Tratamiento intensivo. Considerar ayudas técnicas.'
            }
        elif total >= 16:  # 20-39%
            return {
                'nivel': 'Funcionalidad Severamente Limitada',
                'rango': '16-31 puntos',
                'descripcion': 'Limitaciones severas. Alta dependencia para actividades.',
                'recomendacion': 'URGENTE: Evaluación especializada. Intervención multidisciplinaria.'
            }
        else:  # 0-19%
            return {
                'nivel': 'Funcionalidad Mínima',
                'rango': '0-15 puntos',
                'descripcion': 'Dependencia casi total. Limitación funcional extrema.',
                'recomendacion': 'CRÍTICO: Evaluación médica urgente. Plan de cuidados integral.'
            }


class EvaluacionOswestry(models.Model):
    """
    Índice de Incapacidad de Oswestry (ODI)
    Escala para evaluar el grado de incapacidad por dolor lumbar
    10 secciones, cada una puntúa de 0-5
    Resultado: (suma x 2) = % incapacidad
    """
    
    paciente = models.ForeignKey('Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_oswestry')
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_oswestry')
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    
    # 10 secciones del cuestionario (0-5 cada una)
    seccion_1_intensidad_dolor = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Intensidad del dolor"
    )
    seccion_2_estar_de_pie = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para estar de pie"
    )
    seccion_3_cuidados_personales = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Cuidados personales"
    )
    seccion_4_dormir = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Calidad del sueño"
    )
    seccion_5_levantar_peso = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para levantar peso"
    )
    seccion_6_actividad_sexual = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Actividad sexual"
    )
    seccion_7_andar = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para andar"
    )
    seccion_8_vida_social = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Vida social"
    )
    seccion_9_estar_sentado = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para estar sentado"
    )
    seccion_10_viajar = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="0-5: Capacidad para viajar"
    )
    
    # Notas opcionales
    notas_clinicas = models.TextField(null=True, blank=True, help_text="Observaciones clínicas adicionales")
    
    class Meta:
        verbose_name = "Evaluación Oswestry"
        verbose_name_plural = "Evaluaciones Oswestry"
        ordering = ['-fecha_evaluacion']
        unique_together = []
    
    def __str__(self):
        return f"ODI - {self.paciente.nombre} ({self.fecha_evaluacion.strftime('%d/%m/%Y')})"
    
    def get_total_puntos(self):
        """Calcula la suma total de las 10 secciones"""
        total = (
            self.seccion_1_intensidad_dolor +
            self.seccion_2_estar_de_pie +
            self.seccion_3_cuidados_personales +
            self.seccion_4_dormir +
            self.seccion_5_levantar_peso +
            self.seccion_6_actividad_sexual +
            self.seccion_7_andar +
            self.seccion_8_vida_social +
            self.seccion_9_estar_sentado +
            self.seccion_10_viajar
        )
        return total
    
    def get_porcentaje_incapacidad(self):
        """Calcula el porcentaje de incapacidad (total x 2)"""
        return self.get_total_puntos() * 2
    
    def get_interpretacion(self):
        """Devuelve la interpretación clínica según el porcentaje"""
        porcentaje = self.get_porcentaje_incapacidad()
        
        if porcentaje == 0:
            return {
                'nivel': 'Sin incapacidad',
                'rango': '0%',
                'descripcion': 'Sin limitación funcional. Paciente funcional normal.',
                'recomendacion': 'Mantener actividades normales. Reevaluar periódicamente.'
            }
        elif porcentaje <= 20:
            return {
                'nivel': 'Incapacidad mínima',
                'rango': '0-20%',
                'descripcion': 'Ligeras limitaciones en actividades. Síntomas leves.',
                'recomendacion': 'Continuar actividades con moderación. Educación en ergonomía.'
            }
        elif porcentaje <= 40:
            return {
                'nivel': 'Incapacidad moderada',
                'rango': '20-40%',
                'descripcion': 'Limitaciones moderadas. Interfiere con algunas actividades.',
                'recomendacion': 'Intensificar rehabilitación. Ajustar actividades laborales si es necesario.'
            }
        elif porcentaje <= 60:
            return {
                'nivel': 'Incapacidad severa',
                'rango': '40-60%',
                'descripcion': 'Limitaciones severas. Afecta significativamente la función.',
                'recomendacion': 'Tratamiento intensivo. Considerar referencias especializadas.'
            }
        elif porcentaje <= 80:
            return {
                'nivel': 'Incapacidad muy severa',
                'rango': '60-80%',
                'descripcion': 'Paciente incapacitado para la mayoría de actividades.',
                'recomendacion': 'URGENCIA: Consulta con especialista. Evaluación médica completa.'
            }
        else:
            return {
                'nivel': 'Incapacidad total',
                'rango': '80-100%',
                'descripcion': 'Incapacidad completa. Paciente confinado.',
                'recomendacion': 'CRÍTICO: Evaluación médica urgente. Posible referencia quirúrgica.'
            }


class EvaluacionQuickDASH(models.Model):
    """
    QuickDASH — discapacidad de hombro, codo y mano.
    11 ítems (escala 1–5). Puntuación: ((promedio) - 1) × 25 = % discapacidad.
    Requiere al menos 10 ítems completados.
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_quickdash',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_quickdash',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    notas_clinicas = models.TextField(null=True, blank=True)

    pregunta_1 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_2 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_3 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_4 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_5 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_6 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_7 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_8 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_9 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_10 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pregunta_11 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        verbose_name = 'Evaluación QuickDASH'
        verbose_name_plural = 'Evaluaciones QuickDASH'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'QuickDASH - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")})'

    def _valores(self):
        from .quickdash_data import CAMPOS_QUICKDASH
        return [getattr(self, c) for c in CAMPOS_QUICKDASH]

    def get_porcentaje_discapacidad(self):
        valores = self._valores()
        n = len(valores)
        if n < 10:
            return None
        promedio = sum(valores) / n
        return round((promedio - 1) * 25, 1)

    def get_interpretacion(self):
        pct = self.get_porcentaje_discapacidad()
        if pct is None:
            return {'nivel': 'Incompleto', 'descripcion': 'Faltan ítems para calcular.'}
        if pct <= 20:
            nivel = 'Discapacidad leve'
        elif pct <= 40:
            nivel = 'Discapacidad moderada'
        elif pct <= 60:
            nivel = 'Discapacidad severa'
        else:
            nivel = 'Discapacidad muy severa'
        return {
            'nivel': nivel,
            'porcentaje': pct,
            'descripcion': f'Puntuación QuickDASH: {pct}% de discapacidad (mayor = peor).',
        }


class EvaluacionWOMAC(models.Model):
    """
    WOMAC — dolor, rigidez y función en artrosis de rodilla/cadera.
    24 ítems (0–4). Total 0–96; mayor puntuación = peor afectación.
    """

    paciente = models.ForeignKey(
        'Login.Paciente', on_delete=models.CASCADE, related_name='evaluaciones_womac',
    )
    clinico = models.ForeignKey(
        'Login.Clinico', on_delete=models.CASCADE, related_name='evaluaciones_womac',
    )
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    respuestas = models.JSONField(help_text='Lista de 24 enteros (0–4) en orden WOMAC')
    notas_clinicas = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Evaluación WOMAC'
        verbose_name_plural = 'Evaluaciones WOMAC'
        ordering = ['-fecha_evaluacion']

    def __str__(self):
        return f'WOMAC - {self.paciente.nombre} ({self.fecha_evaluacion.strftime("%d/%m/%Y")})'

    def get_puntaje_dolor(self):
        return sum(self.respuestas[0:5])

    def get_puntaje_rigidez(self):
        return sum(self.respuestas[5:7])

    def get_puntaje_funcion(self):
        return sum(self.respuestas[7:24])

    def get_total_puntos(self):
        return sum(self.respuestas)

    def get_porcentaje_afectacion(self):
        return round((self.get_total_puntos() / 96) * 100, 1)

    def get_interpretacion(self):
        total = self.get_total_puntos()
        if total <= 24:
            nivel = 'Afectación ligera'
        elif total <= 48:
            nivel = 'Afectación moderada'
        elif total <= 72:
            nivel = 'Afectación intensa'
        else:
            nivel = 'Afectación muy intensa'
        return {
            'nivel': nivel,
            'total': total,
            'dolor': self.get_puntaje_dolor(),
            'rigidez': self.get_puntaje_rigidez(),
            'funcion': self.get_puntaje_funcion(),
            'porcentaje': self.get_porcentaje_afectacion(),
            'descripcion': (
                f'Total {total}/96 — Dolor {self.get_puntaje_dolor()}/20, '
                f'Rigidez {self.get_puntaje_rigidez()}/8, '
                f'Función {self.get_puntaje_funcion()}/68.'
            ),
        }

