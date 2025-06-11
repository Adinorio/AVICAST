from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.authentication'

    def ready(self):
        pass

    # Register post_migrate signal for default user creation
    # import src.apps.authentication.signals  # noqa 