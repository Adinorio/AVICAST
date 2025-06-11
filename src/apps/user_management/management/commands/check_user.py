from django.core.management.base import BaseCommand
from src.apps.user_management.models import User
from django.contrib.auth.hashers import make_password
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check if a user exists and create if needed'

    def handle(self, *args, **options):
        user_id = '25-0609-001'
        password = '12345'
        
        # Check if user exists
        try:
            user = User.objects.get(custom_id=user_id)
            self.stdout.write(f'User found with custom_id: {user.custom_id}')
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write(f'Is active: {user.is_active}')
            self.stdout.write(f'Is staff: {user.is_staff}')
            self.stdout.write(f'Is superuser: {user.is_superuser}')
            
            # Update user if needed
            user.username = user_id  # Ensure username matches custom_id
            user.role = 'admin'
            user.is_active = True
            user.is_staff = True
            user.is_superuser = False
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated user {user_id}'))
            
        except User.DoesNotExist:
            self.stdout.write('User not found, creating new user...')
            try:
                # Create new user
                user = User.objects.create(
                    username=user_id,
                    custom_id=user_id,
                    email=f'{user_id}@example.com',
                    role='admin',
                    is_active=True,
                    is_staff=True,
                    is_superuser=False
                )
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Successfully created user {user_id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating user: {str(e)}')) 