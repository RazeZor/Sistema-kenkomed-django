from django.core.management.base import BaseCommand

from clinicas.models import Clinica
from clinicas.services import ClinicaServiceError, unir_clinico_a_centro


class Command(BaseCommand):
    help = (
        'Une un clínico a un centro compartido y migra sus pacientes. '
        'Ejemplo: python manage.py unir_clinico_centro --rut 12345678-9 --clinica-id 2'
    )

    def add_arguments(self, parser):
        parser.add_argument('--rut', required=True, help='RUT del clínico a unir')
        parser.add_argument('--clinica-id', type=int, required=True, help='ID de la clínica destino')
        parser.add_argument(
            '--rol',
            default='miembro',
            choices=['admin', 'miembro'],
            help='Rol del clínico en el centro',
        )
        parser.add_argument(
            '--sin-migrar-pacientes',
            action='store_true',
            help='No mover pacientes de la clínica individual anterior',
        )
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar qué haría')

    def handle(self, *args, **options):
        rut = options['rut']
        clinica_id = options['clinica_id']
        rol = options['rol']
        migrar = not options['sin_migrar_pacientes']
        dry_run = options['dry_run']

        try:
            clinica = Clinica.objects.get(id=clinica_id)
        except Clinica.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'No existe la clínica con id {clinica_id}'))
            return

        self.stdout.write(f'Centro destino: {clinica.nombre} (id={clinica.id}, tipo={clinica.tipo})')
        self.stdout.write(f'Clínico: {rut}')
        self.stdout.write(f'Rol: {rol}')
        self.stdout.write(f'Migrar pacientes: {"sí" if migrar else "no"}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: no se aplicaron cambios.'))
            return

        try:
            resultado = unir_clinico_a_centro(
                clinico_rut=rut,
                clinica_destino_id=clinica_id,
                rol=rol,
                migrar_pacientes=migrar,
            )
        except ClinicaServiceError as exc:
            self.stdout.write(self.style.ERROR(str(exc)))
            return

        clinico = resultado['clinico']
        clinica = resultado['clinica']

        if resultado['ya_estaba']:
            self.stdout.write(self.style.WARNING(
                f'{clinico.nombre} {clinico.apellido} ya pertenece a "{clinica.nombre}".'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'{clinico.nombre} {clinico.apellido} unido a "{clinica.nombre}" '
            f'({resultado["pacientes_migrados"]} pacientes migrados).'
        ))
