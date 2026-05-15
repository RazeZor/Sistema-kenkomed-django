from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

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

