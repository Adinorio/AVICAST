from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)

    @staticmethod
    def create_default_user():
        hashed_password = make_password("Avicast123")
        if not User.objects.filter(user_id="010101").exists():
            User.objects.create(user_id="010101", password=hashed_password)

