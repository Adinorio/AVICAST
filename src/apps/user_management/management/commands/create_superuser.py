from django.core.management.base import BaseCommand
from src.apps.user_management.models import User

class Command(BaseCommand):
    help = 'Creates a superuser with predefined credentials'

    def handle(self, *args, **options):
        # Delete existing superuser if exists
        User.objects.filter(custom_id='010101').delete()
        
        # Create new superuser
        user = User.objects.create(
            username='010101',
            custom_id='010101',
            first_name='Super',
            last_name='Admin',
            role='super_admin',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        user.set_password('12345')
        user.save()
        self.stdout.write(self.style.SUCCESS('Successfully created superuser')) 