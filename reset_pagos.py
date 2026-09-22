import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SistemaKenkoMed.settings')
django.setup()

from pagos.models import RegistroPago, PackAtencion, DeudaPaciente
from Login.models import Paciente
from clinicas.models import Clinica
from pagos.services import recalcular_deuda

print("Borrando RegistroPago...")
RegistroPago.objects.all().delete()

print("Borrando PackAtencion...")
PackAtencion.objects.all().delete()

print("Borrando DeudaPaciente...")
DeudaPaciente.objects.all().delete()

print("Recalculando deudas para reflejar las sesiones puras...")
clinicas = Clinica.objects.all()
for clinica in clinicas:
    pacientes = Paciente.objects.all()
    for paciente in pacientes:
        # Solo recalcular si el paciente tiene alguna sesión en esta clínica
        from SesionesKinesicas.models import SesionKinesica
        tiene_sesiones = SesionKinesica.objects.filter(paciente=paciente, ciclo__clinica=clinica).exists()
        if tiene_sesiones:
            recalcular_deuda(paciente, clinica)

print("¡Todo limpio y recalculado!")