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
    path('family/<int:family_id>/archive/', views.archive_family, name='archive_family'),
    path('species/<int:species_id>/archive/', views.archive_species, name='archive_species'),
    path('family/<int:family_id>/restore/', views.restore_family, name='restore_family'),
    path('species/<int:species_id>/restore/', views.restore_species, name='restore_species'),
    path('edit-family/<int:family_id>/', views.edit_family, name='edit_family'),
    path('help/', views.help_view, name='help'),
    path('image-processing/', views.image_processing_view, name='image_processing'),
    path('image-processing-next/', views.image_processing_next_view, name='image_processing_next'),
    path('review-dashboard/', views.review_dashboard_view, name='review_dashboard'),
    # API for Bird Species
    path('api/birds/add/', views.add_species_view, name='add_species_api'),
    path('api/birds/edit/<int:species_id>/', views.edit_species_view, name='edit_species_api'),
    path('api/families/', views.get_families_api, name='get_families_api'),
    path('api/conservation-statuses/', views.get_conservation_statuses_api, name='get_conservation_statuses_api'),
    path('api/birds/<int:species_id>/', views.get_species_details_api, name='get_species_details_api'),
    # Site URLs
    path('sites/', views.site_list, name='site_list'),
    path('sites/<int:site_id>/', views.site_detail, name='site_detail'),
    path('add-site/', views.add_site, name='add_site'),
    path('edit-site/<int:site_id>/', views.edit_site, name='edit_site'),
    path('delete-site/<int:site_id>/', views.delete_site, name='delete_site'),
    # API for site data
    path('api/sites/<int:site_id>/years/', views.get_site_years, name='get_site_years'),
    path('api/sites/<int:site_id>/months/<int:year>/', views.get_monthly_detections, name='get_monthly_detections'),
    # Report URL
    path('reports/', views.report_view, name='reports'),
]
