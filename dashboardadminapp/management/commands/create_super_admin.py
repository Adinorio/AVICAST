from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from dashboardadminapp.models import User

class Command(BaseCommand):
    help = 'Creates a super admin user'

    def handle(self, *args, **options):
        if not User.objects.filter(custom_id='010101').exists():
            User.objects.create(
                username='superadmin',
                password=make_password('Avicast123'),
                custom_id='010101',
                role='super_admin',
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Successfully created super admin user'))
        else:
            self.stdout.write(self.style.WARNING('Super admin user already exists')) 