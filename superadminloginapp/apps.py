from django.apps import AppConfig

class SuperadminloginappConfig(AppConfig):
    name = 'superadminloginapp'

    def ready(self):
        # Register post_migrate signal for default user creation
        import superadminloginapp.signals  # noqa

