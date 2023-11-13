from django.apps import AppConfig


class PexpressConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'PExpress'

    def ready(self):
        import PExpress.signals
