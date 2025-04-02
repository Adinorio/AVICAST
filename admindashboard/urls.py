from django.urls import path
from .views import dashboard_view,logout_view

app_name = "admindashboard"

urlpatterns = [
    path('dashboard/', dashboard_view, name='dashboard'),  # Route for the dashboard view
    path('logout/', logout_view, name='logout_view'),
]