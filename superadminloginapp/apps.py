from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'superadminloginapp'

    def ready(self):
        from .models import User
        User.create_default_user()
