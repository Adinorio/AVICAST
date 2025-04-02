from django.db import models
from superadminloginapp.models import User
from django.db.models import Max


class Log(models.Model):
    event = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event

def generate_user_id():
    # Generate a custom user ID based on the current maximum ID
    last_user = UserProfile.objects.aggregate(Max('id'))["id__max"] or 0
    new_id = last_user + 1
    return f"25-2409-{new_id:03d}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")  
    custom_user_id = models.CharField(max_length=15, unique=True, null=False, blank=False)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50)
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.custom_user_id:
            self.custom_user_id = generate_user_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


