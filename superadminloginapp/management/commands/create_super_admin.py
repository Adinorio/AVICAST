from django.core.management.base import BaseCommand
from superadminloginapp.models import User
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Creates a super admin user if it does not exist'

    def handle(self, *args, **options):
        user_id = '010101'
        password = 'Avicast123'
        
        if not User.objects.filter(user_id=user_id).exists():
            self.stdout.write('Creating super admin user...')
            User.objects.create(
                user_id=user_id,
                password=make_password(password)
            )
            self.stdout.write(self.style.SUCCESS('Super admin user created successfully'))
        else:
            self.stdout.write('Super admin user already exists')
            
        # Print the user's details
        user = User.objects.get(user_id=user_id)
        self.stdout.write(f'User ID: {user.user_id}')
        self.stdout.write(f'Password hash: {user.password}') 