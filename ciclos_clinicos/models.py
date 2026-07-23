from django.db import models
from django.db.models import Q


class CicloClinico(models.Model):
    """Episodio de tratamiento kinésico de un paciente en una clínica."""

    ESTADO_ACTIVO = 'activo'
    ESTADO_FINALIZADO = 'finalizado'
    ESTADO_ABANDONADO = 'abandonado'
    ESTADOS = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_FINALIZADO, 'Finalizado'),
        (ESTADO_ABANDONADO, 'Abandonado'),
    ]

    paciente = models.ForeignKey(
        'Login.Paciente',
        on_delete=models.CASCADE,
        related_name='ciclos_clinicos',
    )
    clinica = models.ForeignKey(
        'clinicas.Clinica',
        on_delete=models.CASCADE,
        related_name='ciclos_clinicos',
    )
    clinico_responsable = models.ForeignKey(
        'Login.Clinico',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ciclos_a_cargo',
    )
    numero_ciclo = models.PositiveIntegerField(verbose_name='Número de ciclo')
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_ACTIVO)
    motivo_consulta = models.TextField(blank=True, default='')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    notas_cierre = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Ciclo clínico'
        verbose_name_plural = 'Ciclos clínicos'
        ordering = ['-numero_ciclo']
        unique_together = [('paciente', 'clinica', 'numero_ciclo')]
        indexes = [
            models.Index(fields=['paciente', 'estado']),
            models.Index(fields=['clinica', '-fecha_inicio']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['paciente', 'clinica'],
                condition=Q(estado='activo'),
                name='unico_ciclo_activo_por_paciente_clinica',
            ),
        ]

    def __str__(self):
        return (
            f'Ciclo #{self.numero_ciclo} — {self.paciente.nombre} {self.paciente.apellido} '
            f'({self.get_estado_display()})'
        )

    @property
    def es_activo(self):
        return self.estado == self.ESTADO_ACTIVO

    @property
    def es_solo_lectura(self):
        return self.estado in (self.ESTADO_FINALIZADO, self.ESTADO_ABANDONADO)

    def etiqueta_display(self):
        return f'Ciclo #{self.numero_ciclo} — {self.get_estado_display()}'
