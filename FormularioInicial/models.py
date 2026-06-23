from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta

class TokenFormulario(models.Model):
    """Token vinculado a un paciente pre-registrado para formulario remoto de anamnesis."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='tokens_formulario')
    paciente = models.ForeignKey('Login.Paciente', on_delete=models.CASCADE, related_name='tokens_formulario', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    usado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token de Formulario"
        verbose_name_plural = "Tokens de Formularios"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Token {self.id} - {self.paciente.nombre} {self.paciente.apellido}"
    
    def is_expired(self):
        if not self.fecha_expiracion:
            return False
        return timezone.now() > self.fecha_expiracion
    
    def is_valid(self):
        return self.activo and not self.is_expired() and not self.usado
    
    def marcar_como_usado(self):
        self.usado = True
        self.save()
    
    def desactivar(self):
        self.activo = False
        self.save()
    
    @classmethod
    def crear_token(cls, clinico, paciente, dias_expiracion=7):
        fecha_expiracion = timezone.now() + timedelta(days=dias_expiracion)
        return cls.objects.create(
            clinico=clinico,
            paciente=paciente,
            fecha_expiracion=fecha_expiracion
        )


class ConsentimientoDatos(models.Model):
    """Registro de aceptación del aviso de tratamiento de datos."""

    ORIGEN_CHOICES = [
        ('formulario_qr', 'Formulario QR'),
        ('alta_panel', 'Alta en panel'),
    ]

    paciente = models.ForeignKey('Login.Paciente', on_delete=models.CASCADE, related_name='consentimientos')
    clinica = models.ForeignKey('clinicas.Clinica', on_delete=models.SET_NULL, null=True, blank=True)
    origen = models.CharField(max_length=30, choices=ORIGEN_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    token = models.ForeignKey(
        TokenFormulario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consentimientos',
    )

    class Meta:
        verbose_name = 'Consentimiento de datos'
        verbose_name_plural = 'Consentimientos de datos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.paciente.rut} — {self.get_origen_display()} — {self.fecha:%Y-%m-%d %H:%M}'
