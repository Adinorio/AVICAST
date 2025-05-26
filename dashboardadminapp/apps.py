from django.apps import AppConfig


class DashboardadminappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboardadminapp'

class YourAppConfig(AppConfig):
    name = 'dashboardadminapp'

    def ready(self):
        import dashboardadminapp.signals