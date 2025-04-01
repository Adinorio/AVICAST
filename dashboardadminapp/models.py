from django.db import models
from django.contrib.auth.models import User

class Log(models.Model):
    event = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50)  # "Admin" or "User"
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)  # Active/Disabled users
    is_archived = models.BooleanField(default=False)  # ✅ NEW FIELD

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"