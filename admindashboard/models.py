from django.db import models
from django.db import models
from django.contrib.auth.hashers import make_password

class AdminUser(models.Model):
    ID_number = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)

    @staticmethod
    def generate_next_id():
        # Retrieve the last admin user (ordered by ID_number)
        last_admin = AdminUser.objects.order_by('-ID_number').first()
        if last_admin:
            # Assuming the ID_number format is "25-2410-12XX" where XX are digits
            last_digits = int(last_admin.ID_number.split('-')[-1])
            new_digits = last_digits + 1
        else:
            new_digits = 1
        return f"25-2410-{new_digits:02d}"

    @staticmethod
    def create_default_admin():
        hashed_password = make_password("Admin123")
        default_id = "25-2410-12"  # Starting point
        if not AdminUser.objects.filter(ID_number=default_id).exists():
            AdminUser.objects.create(ID_number=default_id, password=hashed_password)

# Create your models here.
