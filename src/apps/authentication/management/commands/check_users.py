from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import check_password, make_password
from src.apps.authentication.models import User as OldUser
from src.apps.user_management.models import User as NewUser

class Command(BaseCommand):
    help = 'Checks both user models for the super admin user'

    def handle(self, *args, **options):
        user_id = '010101'
        
        # Check old model
        try:
            old_user = OldUser.objects.get(user_id=user_id)
            self.stdout.write('Old User exists:')
            self.stdout.write(f'User ID: {old_user.user_id}')
            self.stdout.write(f'Password hash: {old_user.password}')
        except OldUser.DoesNotExist:
            self.stdout.write('Old User does not exist')
            
        # Check new model
        try:
            new_user = NewUser.objects.get(custom_id=user_id)
            self.stdout.write('\nNew User exists:')
            self.stdout.write(f'Username: {new_user.username}')
            self.stdout.write(f'Custom ID: {new_user.custom_id}')
            self.stdout.write(f'Role: {new_user.role}')
            self.stdout.write(f'Is active: {new_user.is_active}')
            self.stdout.write(f'Is staff: {new_user.is_staff}')
            self.stdout.write(f'Is superuser: {new_user.is_superuser}')
        except NewUser.DoesNotExist:
            self.stdout.write('\nNew User does not exist') 