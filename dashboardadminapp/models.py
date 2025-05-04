from django.db import models
from superadminloginapp.models import User
from django.db.models import Max

class Log(models.Model):
    event = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    custom_user_id = models.CharField(max_length=15, unique=True, null=False, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50)
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)

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


