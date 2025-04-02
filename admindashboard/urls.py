from django.urls import path
from .views import dashboard_view

app_name = "admindashboard"

urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),  # Route for the dashboard view
]