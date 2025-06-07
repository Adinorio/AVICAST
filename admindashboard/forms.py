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
        fields = ['family', 'common_name', 'scientific_name', 'description', 'conservation_status']
        widgets = {
            'family': forms.Select(attrs={'class': 'form-control'}),
            'common_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Common Name'}),
            'scientific_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Scientific Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 2}),
            'conservation_status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Conservation Status'}),
        }

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['name', 'code', 'location', 'description', 'status', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Site Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Site Code'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
