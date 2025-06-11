from django.db.models.signals import post_migrate
from django.dispatch import receiver

def create_default_user(sender, **kwargs):
    from .models import User
    User.create_default_user()

# Connect the signal
post_migrate.connect(create_default_user) 