from django.urls import path
from .views import dashboard_view, logout_view, bird_identification_view, process_bird_image

app_name = "admindashboard"

urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout_view'),
    path('bird_identification/', bird_identification_view, name='bird_identification'),
    path('api/process_bird_image/', process_bird_image, name='process_bird_image'),  # API endpoint for image processing
]
