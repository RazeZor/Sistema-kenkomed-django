from django.db import models

class Clinica(models.Model):
    nombre = models.CharField(max_length=150)
    rut_empresa = models.CharField(max_length=12, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    ciudad = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    TIPO_CHOICES = [
        ('individual', 'Profesional Individual'),
        ('clinica', 'Clínica / Centro'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='individual')
    max_clinicos = models.PositiveIntegerField(default=1)
    logo = models.ImageField(
        upload_to='clinicas/logos/',
        blank=True,
        null=True,
        verbose_name='Logo del centro',
        help_text='Se usa en correos e informes. Si no hay logo, se muestra KenkoMed.',
    )

    def __str__(self):
        return self.nombre


class MembresiaClinica(models.Model):
    ROL_CHOICES = [
        ('admin', 'Administrador de Clínica'),
        ('miembro', 'Miembro'),
    ]
    
    clinico = models.ForeignKey('Login.Clinico', on_delete=models.CASCADE, related_name='membresias')
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='miembros')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, blank=True, null=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('clinico', 'clinica')

    def __str__(self):
        return f"{self.clinico.nombre} {self.clinico.apellido} en {self.clinica.nombre} ({self.rol})"
