from django.apps import AppConfig

class SuperadminloginappConfig(AppConfig):
    name = 'superadminloginapp'

    def ready(self):
        # Ensure that the default user is created when the app starts
        from .models import User
        User.create_default_user()

