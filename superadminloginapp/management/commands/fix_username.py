from django.core.management.base import BaseCommand
from dashboardadminapp.models import User as NewUser

class Command(BaseCommand):
    help = 'Fixes the username of the super admin user'

    def handle(self, *args, **options):
        try:
            user = NewUser.objects.get(custom_id='010101')
            self.stdout.write(f'Found user with ID: {user.id}')
            self.stdout.write(f'Current username: {user.username}')
            
            # Update the username
            user.username = '010101'
            user.save()
            
            self.stdout.write(f'Updated username to: {user.username}')
            self.stdout.write(self.style.SUCCESS('Successfully updated username'))
        except NewUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 