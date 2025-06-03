from django import forms
from .models import Family, Species

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Family Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 2}),
        }

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ['name', 'scientific_name', 'iucn_status', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Species Name'}),
            'scientific_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scientific Name'}),
            'iucn_status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IUCN Status'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
