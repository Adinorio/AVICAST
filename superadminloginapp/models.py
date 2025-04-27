from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    
    @staticmethod
    def create_default_user():
        hashed_password = make_password("Avicast123")
        user, created = User.objects.get_or_create(
            user_id="010101",
            defaults={"password": hashed_password}
        )
        return user  # Optional: Return user instance


