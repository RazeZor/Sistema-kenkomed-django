from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from Login.models import Clinico


def normalizar_rut(rut):
    """Quita puntos y guión, deja cuerpo + dígito verificador en minúsculas."""
    if not rut:
        return ''
    return rut.strip().replace('.', '').replace('-', '').lower()


def referencias_a_clinico():
    """Modelos y columnas FK que apuntan a Login.Clinico."""
    refs = []
    for model in apps.get_models():
        if model is Clinico:
            continue
        for field in model._meta.fields:
            remote = getattr(field, 'remote_field', None)
            if remote and remote.model is Clinico:
                refs.append((model, field.column))
    return refs


def _set_foreign_key_checks(enabled):
    with connection.cursor() as cursor:
        if connection.vendor == 'mysql':
            cursor.execute(f'SET FOREIGN_KEY_CHECKS={1 if enabled else 0}')
        elif connection.vendor == 'sqlite':
            cursor.execute(f'PRAGMA foreign_keys = {"ON" if enabled else "OFF"}')


class Command(BaseCommand):
    help = (
        'Cambia el RUT (clave primaria) de un clínico y actualiza todas las referencias. '
        'Ejemplo: python manage.py cambiar_rut_clinico --actual 21442979 --nuevo 21.442.979-9'
    )

    def add_arguments(self, parser):
        parser.add_argument('--actual', required=True, help='RUT actual del clínico')
        parser.add_argument('--nuevo', required=True, help='RUT nuevo (puede ir con puntos y guión)')
        parser.add_argument('--dry-run', action='store_true', help='Solo muestra qué se actualizaría')
        parser.add_argument('--yes', action='store_true', help='Aplicar sin confirmación interactiva')

    def handle(self, *args, **options):
        rut_actual = options['actual'].strip()
        rut_nuevo = options['nuevo'].strip()
        dry_run = options['dry_run']
        auto_yes = options['yes']

        if rut_actual == rut_nuevo:
            raise CommandError('El RUT nuevo es idéntico al actual.')

        try:
            clinico = Clinico.objects.get(rut=rut_actual)
        except Clinico.DoesNotExist:
            cuerpo = normalizar_rut(rut_actual)
            candidatos = list(
                Clinico.objects.exclude(rut=rut_actual).values_list('rut', flat=True)
            )
            candidatos = [r for r in candidatos if normalizar_rut(r) == cuerpo] or candidatos[:5]
            msg = f'No existe clínico con RUT exacto "{rut_actual}".'
            if candidatos:
                msg += f' En BD: {", ".join(candidatos)}'
            raise CommandError(msg)

        if Clinico.objects.filter(rut=rut_nuevo).exists():
            raise CommandError(f'Ya existe un clínico con RUT "{rut_nuevo}".')

        refs = referencias_a_clinico()
        resumen = []
        total = 0
        for model, column in refs:
            count = model.objects.filter(**{column: rut_actual}).count()
            if count:
                resumen.append(f'  {model._meta.label}: {count} registro(s) en {column}')
                total += count

        self.stdout.write(f'Clínico: {clinico.nombre} {clinico.apellido}')
        self.stdout.write(f'RUT actual:  {rut_actual}')
        self.stdout.write(f'RUT nuevo:   {rut_nuevo}')
        if normalizar_rut(rut_actual) == normalizar_rut(rut_nuevo):
            self.stdout.write('Nota: mismo RUT, solo cambia el formato guardado.')
        self.stdout.write(f'Referencias a actualizar: {total}')
        for linea in resumen:
            self.stdout.write(linea)

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: no se aplicaron cambios.'))
            return

        if not auto_yes:
            confirm = input('¿Aplicar el cambio de RUT? (y/N): ').strip().lower()
            if confirm != 'y':
                self.stdout.write(self.style.ERROR('Operación cancelada.'))
                return

        with transaction.atomic():
            _set_foreign_key_checks(False)
            try:
                for model, column in refs:
                    model.objects.filter(**{column: rut_actual}).update(**{column: rut_nuevo})

                filas = Clinico.objects.filter(rut=rut_actual).update(rut=rut_nuevo)
                if filas != 1:
                    raise CommandError(f'Se esperaba actualizar 1 clínico, se actualizaron {filas}.')
            finally:
                _set_foreign_key_checks(True)

        self.stdout.write(
            self.style.SUCCESS(
                f'RUT actualizado correctamente a "{rut_nuevo}" ({clinico.nombre} {clinico.apellido}).'
            )
        )
