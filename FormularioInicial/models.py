from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class TokenFormulario(models.Model):
    """Modelo para manejar tokens de formularios QR"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='tokens_formulario')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    usado = models.BooleanField(default=False)
    paciente_asociado = models.ForeignKey('Login.Paciente', on_delete=models.SET_NULL, null=True, blank=True, related_name='token_formulario')
    
    class Meta:
        verbose_name = "Token de Formulario"
        verbose_name_plural = "Tokens de Formularios"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Token {self.id} - {self.clinico.nombre} {self.clinico.apellido}"
    
    def is_expired(self):
        """Verifica si el token ha expirado"""
        return timezone.now() > self.fecha_expiracion
    
    def is_valid(self):
        """Verifica si el token es válido (activo, no expirado, no usado)"""
        return self.activo and not self.is_expired() and not self.usado
    
    def marcar_como_usado(self, paciente=None):
        """Marca el token como usado y asocia un paciente si se proporciona"""
        self.usado = True
        if paciente:
            self.paciente_asociado = paciente
        self.save()
    
    def desactivar(self):
        """Desactiva el token"""
        self.activo = False
        self.save()
    
    @classmethod
    def crear_token(cls, clinico, dias_expiracion=7):
        """Crea un nuevo token con fecha de expiración"""
        fecha_expiracion = timezone.now() + timedelta(days=dias_expiracion)
        return cls.objects.create(
            clinico=clinico,
            fecha_expiracion=fecha_expiracion
        )
