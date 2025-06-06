from django.urls import path
from . import views

app_name = 'admindashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('help/', views.help_view, name='help'),
    path('logout/', views.logout_view, name='logout_view'),
    
    # Bird List URLs
    path('birds/', views.bird_list, name='bird_list'),
    path('birds/family/add/', views.add_family, name='add_family'),
    path('birds/family/<int:family_id>/edit/', views.edit_family, name='edit_family'),
    path('birds/family/<int:family_id>/archive/', views.archive_family, name='archive_family'),
    path('birds/family/<int:family_id>/restore/', views.restore_family, name='restore_family'),
    
    path('birds/species/<int:family_id>/add/', views.add_species, name='add_species'),
    path('birds/species/<int:species_id>/edit/', views.edit_species, name='edit_species'),
    path('birds/species/<int:species_id>/archive/', views.archive_species, name='archive_species'),
    path('birds/species/<int:species_id>/restore/', views.restore_species, name='restore_species'),
    path('birds/species/<int:family_id>/list/', views.get_species, name='get_species'),
    
    # Bird Identification URLs
    path('identify/', views.identify_bird, name='identify_bird'),
    path('bird_identification/', views.identify_bird, name='bird_identification'),  # For backward compatibility
]
