from django.apps import AppConfig

class GestionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion'  # remplacer par le nom réel de ton app

    def ready(self):
        # importer les signals pour les enregistrer
        import gestion.signals  # noqa: F401
