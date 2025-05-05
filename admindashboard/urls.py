from django.urls import path
from .views import dashboard_view, logout_view, bird_identification_view, process_bird_image
from . import views

app_name = "admindashboard"

urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout_view'),
    path('bird_identification/', bird_identification_view, name='bird_identification'),
    path('api/process_bird_image/', process_bird_image, name='process_bird_image'),  # API endpoint for image processing
    path('', views.bird_list, name='bird_list'),
    path('family/add/', views.add_family, name='add_family'),
    path('family/<int:family_id>/archive/', views.toggle_family_archive, name='toggle_family'),
    path('species/<int:family_id>/add/', views.add_species, name='add_species'),
    path('species/<int:species_id>/archive/', views.toggle_species_archive, name='toggle_species'),
]
