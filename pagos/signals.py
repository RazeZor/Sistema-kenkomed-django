from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from SesionesKinesicas.models import SesionKinesica
from pagos.services import recalcular_deuda

@receiver(post_save, sender=SesionKinesica)
@receiver(post_delete, sender=SesionKinesica)
def actualizar_deuda_paciente(sender, instance, **kwargs):
    """
    Cada vez que se crea, modifica o elimina una sesión kinésica,
    notificamos al módulo de pagos para que recalcule la deuda del paciente.
    """
    if instance.paciente and getattr(instance, 'ciclo', None) and instance.ciclo.clinica:
        # Se llama a la función pura del módulo de pagos para recalcular
        recalcular_deuda(instance.paciente, instance.ciclo.clinica)
