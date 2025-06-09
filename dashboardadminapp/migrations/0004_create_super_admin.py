from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_super_admin(apps, schema_editor):
    User = apps.get_model('dashboardadminapp', 'User')
    User.objects.create(
        username='superadmin',
        password=make_password('Avicast123'),
        custom_id='010101',
        role='super_admin',
        is_active=True,
        is_staff=True,
        is_superuser=True
    )

def remove_super_admin(apps, schema_editor):
    User = apps.get_model('dashboardadminapp', 'User')
    User.objects.filter(custom_id='010101').delete()

class Migration(migrations.Migration):
    dependencies = [
        ('dashboardadminapp', '0003_user_custom_id_alter_user_role'),
    ]

    operations = [
        migrations.RunPython(create_super_admin, remove_super_admin),
    ] 