from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('FIELD_WORKER', 'Field Worker'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FIELD_WORKER')
    # Add any extra fields as needed (e.g., is_active, is_archived, etc.)
    is_archived = models.BooleanField(default=False)
    last_active = models.DateTimeField(null=True, blank=True)

    def clean(self):
        if self.role == 'SUPER_ADMIN':
            qs = User.objects.filter(role='SUPER_ADMIN')
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError('Only one Super Admin is allowed.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
