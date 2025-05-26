from django import forms
from .models import Family, Species

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['name', 'description']

class SpeciesForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ['family', 'name']
