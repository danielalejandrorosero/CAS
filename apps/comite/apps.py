from django.apps import AppConfig


class ComiteConfig(AppConfig):
    """Configuración de la aplicación Comité"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.comite'
    verbose_name = 'Gestión de Citaciones a Comité'
    
    def ready(self):
        """Configuración cuando la aplicación está lista"""
        try:
            import apps.comite.signals  # noqa F401
        except ImportError:
            pass
