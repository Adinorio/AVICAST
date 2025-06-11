from django.db import models
from django.contrib.auth.hashers import make_password
 
class User(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    password_changed_at = models.DateTimeField(null=True, blank=True) 