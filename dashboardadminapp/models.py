from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Max
from django.utils import timezone
import datetime

# New models will be implemented here

class Log(models.Model):
    event = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event

class User(AbstractUser):
    USER_ROLES = (
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('field_worker', 'Field Worker'),
    )
    
    custom_id = models.CharField(max_length=12, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='field_worker')
    date_created = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Add related_name to avoid conflicts with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='dashboard_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='dashboard_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    class Meta:
        ordering = ['-date_created']
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.custom_id or self.username})"

    def save(self, *args, **kwargs):
        if not self.custom_id:
            # Generate custom ID
            today = datetime.datetime.now()
            year = str(today.year)[-2:]  # Get last 2 digits of year
            month = str(today.month).zfill(2)  # Month with leading zero
            day = str(today.day).zfill(2)  # Day with leading zero
            
            # Get the latest sequence number for today
            latest_user = User.objects.filter(
                custom_id__startswith=f"{year}-{month}{day}"
            ).order_by('-custom_id').first()
            
            if latest_user:
                # Extract the sequence number and increment
                sequence = int(latest_user.custom_id.split('-')[-1]) + 1
            else:
                sequence = 1
                
            # Format: YY-MMDD-XXX
            self.custom_id = f"{year}-{month}{day}-{str(sequence).zfill(3)}"
            
        super().save(*args, **kwargs)

    def has_dashboard_access(self):
        """Check if user has access to dashboardadminapp"""
        return self.role == 'super_admin'

    def has_admin_dashboard_access(self):
        """Check if user has access to admindashboardapp"""
        return self.role in ['admin', 'field_worker']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    custom_user_id = models.CharField(max_length=15, unique=True, null=False, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50)
    last_active = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # On initial save, assign a custom_user_id based on numeric PK
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.custom_user_id:
            self.custom_user_id = f"25-2409-{self.id:03d}"
            # update only the custom_user_id field
            super().save(update_fields=['custom_user_id'])

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

def generate_user_id():
    # If you ever need to know "what the next custom ID would be" without saving:
    last = UserProfile.objects.aggregate(Max('custom_user_id'))["custom_user_id__max"]
    if last:
        n = int(last.split('-')[-1]) + 1
    else:
        n = 1
    return f"25-2409-{n:03d}"

# Add new model for Permission Settings
class PermissionSetting(models.Model):
    # Role to which this permission applies
    role = models.CharField(max_length=20, choices=User.USER_ROLES, unique=True)

    # Accessibility permissions
    view_report_management = models.BooleanField(default=True)
    view_species_management = models.BooleanField(default=True)
    view_site_management = models.BooleanField(default=True)
    view_bird_census_management = models.BooleanField(default=True)
    view_image_processing = models.BooleanField(default=True)

    # Option permissions
    generate_reports = models.BooleanField(default=True)
    modify_data = models.BooleanField(default=True)
    add_sites = models.BooleanField(default=True)
    add_birds = models.BooleanField(default=True)
    generate_data = models.BooleanField(default=True)

    def __str__(self):
        return f"Permissions for {self.role}"

    class Meta:
        verbose_name = "Permission Setting"
        verbose_name_plural = "Permission Settings"


