from django.apps import AppConfig


class ClinicasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinicas'

    def ready(self):
        import clinicas.signals  # noqa: F401
