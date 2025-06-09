from django.core.management.base import BaseCommand
from dashboardadminapp.models import User as NewUser

class Command(BaseCommand):
    help = 'Checks for duplicate users in the new model'

    def handle(self, *args, **options):
        # Check for duplicate usernames
        usernames = {}
        for user in NewUser.objects.all():
            if user.username in usernames:
                self.stdout.write(f'Duplicate username found: {user.username}')
                self.stdout.write(f'First user: {usernames[user.username].id}')
                self.stdout.write(f'Second user: {user.id}')
            else:
                usernames[user.username] = user
                
        # Check for duplicate custom_ids
        custom_ids = {}
        for user in NewUser.objects.all():
            if user.custom_id in custom_ids:
                self.stdout.write(f'Duplicate custom_id found: {user.custom_id}')
                self.stdout.write(f'First user: {custom_ids[user.custom_id].id}')
                self.stdout.write(f'Second user: {user.id}')
            else:
                custom_ids[user.custom_id] = user
                
        # Print all users
        self.stdout.write('\nAll users in new model:')
        for user in NewUser.objects.all():
            self.stdout.write(f'ID: {user.id}')
            self.stdout.write(f'Username: {user.username}')
            self.stdout.write(f'Custom ID: {user.custom_id}')
            self.stdout.write(f'Role: {user.role}')
            self.stdout.write('---') 