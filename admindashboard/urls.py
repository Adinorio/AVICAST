from django.urls import path
from . import views

app_name = "admindashboard"

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('bird-identification/', views.bird_identification_view, name='bird_identification'),
    path('api/process_bird_image/', views.process_bird_image, name='process_bird_image'),
    path('bird-list/', views.bird_list, name='bird_list'),
    path('add-family/', views.add_family, name='add_family'),
    path('add-species/<int:family_id>/', views.add_species, name='add_species'),
    path('family/<int:family_id>/archive/', views.archive_family, name='archive_family'),
    path('species/<int:species_id>/archive/', views.archive_species, name='archive_species'),
    path('family/<int:family_id>/restore/', views.restore_family, name='restore_family'),
    path('species/<int:species_id>/restore/', views.restore_species, name='restore_species'),
    path('edit-family/<int:family_id>/', views.edit_family, name='edit_family'),
    path('edit-species/<int:species_id>/', views.edit_species, name='edit_species'),
    path('help/', views.help_view, name='help'),
    path('image-processing/', views.image_processing_view, name='image_processing'),
    path('image-processing-next/', views.image_processing_next_view, name='image_processing_next'),
    path('review-dashboard/', views.review_dashboard_view, name='review_dashboard'),
]
