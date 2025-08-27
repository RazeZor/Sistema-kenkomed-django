from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import identify_hasher
from django.db import transaction

from Login.models import Clinico


def looks_like_hash(s):
    if not s:
        return False
    try:
        identify_hasher(s)
        return True
    except Exception:
        return False


class Command(BaseCommand):
    help = 'Hash plain-text Clinico passwords stored in the DB. Use --dry-run to preview, --yes to apply.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False, help='Show which records would be updated without changing DB')
        parser.add_argument('--yes', action='store_true', default=False, help='Apply changes without interactive confirmation')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        auto_yes = options['yes']

        clinicos = Clinico.objects.all()
        to_update = []

        for c in clinicos:
            pw = c.contraseña or ''
            if not pw:
                continue
            if looks_like_hash(pw):
                continue
            to_update.append(c)

        total = clinicos.count()
        count_update = len(to_update)

        self.stdout.write(f'Total clinicos: {total}')
        self.stdout.write(f'Clinicos a hashear: {count_update}')

        if count_update == 0:
            self.stdout.write(self.style.SUCCESS('No se encontraron contraseñas en texto plano.'))
            return

        for c in to_update:
            self.stdout.write(f' - {c.rut} ({c.nombre} {c.apellido})')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: no se aplicarán cambios.'))
            return

        if not auto_yes:
            confirm = input('Proceder a hashear las contraseñas listadas arriba? (y/N): ').strip().lower()
            if confirm != 'y':
                self.stdout.write(self.style.ERROR('Operación cancelada por el usuario.'))
                return

        # Aplicar cambios en una transacción
        with transaction.atomic():
            for c in to_update:
                raw = c.contraseña or ''
                # Usar el helper del modelo si está disponible
                if hasattr(c, 'set_password'):
                    c.set_password(raw)
                else:
                    # Fallback: intentar usar el hasher directamente
                    from django.contrib.auth.hashers import make_password
                    c.contraseña = make_password(raw)
                c.save()

        self.stdout.write(self.style.SUCCESS(f'Hasheado {count_update} contraseñas correctamente.'))
