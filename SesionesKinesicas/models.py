from django.db import models
from Login.models import Paciente, Clinico


class SesionKinesica(models.Model):
    """
    Modelo para registrar sesiones kinésicas de un paciente.
    La primera sesión contiene una evaluación inicial detallada.
    Las sesiones posteriores contienen solo notas clínicas y evolución.
    """
    
    # Relaciones
    paciente = models.ForeignKey(
        Paciente, 
        on_delete=models.CASCADE, 
        related_name='sesiones_kinesicas'
    )
    clinico = models.ForeignKey(
        Clinico, 
        on_delete=models.CASCADE, 
        related_name='sesiones_kinesicas_realizadas'
    )
    
    # Información de la sesión
    numero_sesion = models.PositiveIntegerField(
        verbose_name="Número de Sesión",
        help_text="Número secuencial de la sesión"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_ultima_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Actualización"
    )
    
    # Evaluación Inicial (solo en la primera sesión)
    # Se puede usar un JSON para almacenar múltiples campos del cuestionario
    evaluacion_inicial = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Evaluación Inicial",
        help_text="Cuestionario detallado de la primera sesión"
    )
    
    # Notas clínicas (texto libre)
    notas_clinicas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas Clínicas",
        help_text="Notas clínicas del clínico sobre el paciente"
    )
    
    # Evolución (texto libre)
    evolucion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Evolución",
        help_text="Descripción de la evolución del paciente en esta sesión"
    )
    
    # Indicador de primera sesión
    es_primera_sesion = models.BooleanField(
        default=False,
        verbose_name="Es Primera Sesión"
    )
    
    class Meta:
        verbose_name = "Sesión Kinésica"
        verbose_name_plural = "Sesiones Kinésicas"
        ordering = ['-numero_sesion']
        unique_together = ('paciente', 'numero_sesion')
        indexes = [
            models.Index(fields=['paciente', '-numero_sesion']),
            models.Index(fields=['clinico', 'fecha_creacion']),
        ]
    
    def __str__(self):
        sesion_type = "Inicial" if self.es_primera_sesion else "Sesión"
        return f"{sesion_type} #{self.numero_sesion} - {self.paciente.nombre} {self.paciente.apellido} ({self.fecha_creacion.strftime('%d/%m/%Y')})"
    
    def get_siguiente_numero_sesion(self):
        """Retorna el número que debería tener la siguiente sesión"""
        ultima_sesion = SesionKinesica.objects.filter(
            paciente=self.paciente
        ).order_by('-numero_sesion').first()
        
        if ultima_sesion:
            return ultima_sesion.numero_sesion + 1
        return 1
