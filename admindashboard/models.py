from django.db import models
from django.contrib.auth.hashers import make_password
from django import forms
from django.utils import timezone

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

    def __str__(self):
        return self.ID_number

class Family(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Species(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='species')
    name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255)
    iucn_status = models.CharField(max_length=50)
    is_archived = models.BooleanField(default=False)
    image = models.ImageField(upload_to='species_images/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class BirdDetection(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='detections')
    image = models.ImageField(upload_to='detection_images/')
    confidence = models.FloatField()
    detection_date = models.DateTimeField(default=timezone.now)
    coordinates = models.JSONField()  # Store bounding box coordinates

    def __str__(self):
        return f"{self.species.name} - {self.detection_date}"

### forms.py
from django import forms
from .models import Family, Species

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Family Name'}),
            'description': forms.Textarea(attrs={'class':'form-control','placeholder':'Description','rows':2}),
        }

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ['name','scientific_name','iucn_status','image']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','placeholder':'Species Name'}),
            'scientific_name': forms.TextInput(attrs={'class':'form-control','placeholder':'Scientific Name'}),
            'iucn_status': forms.TextInput(attrs={'class':'form-control','placeholder':'IUCN Status'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
# Create your models here.
