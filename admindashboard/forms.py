from django import forms
from .models import Family, Species, Site

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Family Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Family Description', 'rows': 3}),
        }

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ['family', 'common_name', 'scientific_name', 'description', 'conservation_status', 'image']
        widgets = {
            'family': forms.Select(attrs={'class': 'form-control'}),
            'common_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Common Name'}),
            'scientific_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scientific Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 2}),
            'conservation_status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Conservation Status'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name', 'location', 'status', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Site Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Location'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
