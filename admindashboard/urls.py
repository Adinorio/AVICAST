from django.urls import path
from . import views

app_name = "admindashboard"

urlpatterns = [
    path("", views.admin_dashboard, name="dashboard"),
]
