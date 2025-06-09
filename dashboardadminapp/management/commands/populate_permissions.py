from django.core.management.base import BaseCommand
from dashboardadminapp.models import PermissionSetting, User

class Command(BaseCommand):
    help = 'Populates default permission settings for Admin and Field Worker roles.'

    def handle(self, *args, **options):
        # Define default permissions for Admin
        admin_defaults = {
            'view_report_management': True,
            'generate_reports': True,
            'view_species_management': True,
            'modify_data': True,
            'view_site_management': True,
            'add_sites': True,
            'view_bird_census_management': True,
            'add_birds': True,
            'view_image_processing': True,
            'generate_data': True,
        }
        
        # Define default permissions for Field Worker (all False initially, or adjust as needed)
        field_worker_defaults = {
            'view_report_management': False,
            'generate_reports': False,
            'view_species_management': False,
            'modify_data': False,
            'view_site_management': False,
            'add_sites': False,
            'view_bird_census_management': False,
            'add_birds': False,
            'view_image_processing': False,
            'generate_data': False,
        }

        # Create or update Admin permissions
        admin_permissions, created = PermissionSetting.objects.update_or_create(
            role='admin',
            defaults=admin_defaults
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created default permissions for Admin.'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated default permissions for Admin.'))

        # Create or update Field Worker permissions
        field_worker_permissions, created = PermissionSetting.objects.update_or_create(
            role='field_worker',
            defaults=field_worker_defaults
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created default permissions for Field Worker.'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated default permissions for Field Worker.'))

        # Update counts for stats cards
        num_admins = User.objects.filter(role='admin').count()
        num_field_workers = User.objects.filter(role='field_worker').count()
        self.stdout.write(self.style.SUCCESS(f'Current Admin count: {num_admins}'))
        self.stdout.write(self.style.SUCCESS(f'Current Field Worker count: {num_field_workers}')) 