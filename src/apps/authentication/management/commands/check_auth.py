from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from src.apps.user_management.models import User as NewUser
from src.apps.authentication.models import User as OldUser
from django.contrib.auth.hashers import check_password, make_password

class Command(BaseCommand):
    help = 'Checks authentication for both user models'

    def handle(self, *args, **options):
        user_id = '010101'
        password = 'Avicast123'
        
        # Check old model
        try:
            old_user = OldUser.objects.get(user_id=user_id)
            self.stdout.write('Old User exists:')
            self.stdout.write(f'User ID: {old_user.user_id}')
            self.stdout.write(f'Password hash: {old_user.password}')
            self.stdout.write(f'Password check: {check_password(password, old_user.password)}')
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
            
            # Create a test password hash
            test_hash = make_password(password)
            self.stdout.write(f'\nTest password hash: {test_hash}')
            self.stdout.write(f'Password check: {check_password(password, new_user.password)}')
        except NewUser.DoesNotExist:
            self.stdout.write('\nNew User does not exist') 