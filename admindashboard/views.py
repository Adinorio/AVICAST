from django.shortcuts import render
from dashboardadminapp.models import UserProfile

# Simple dashboard view without login required
def dashboard_view(request):
    return render(request, "admindashboard/dashboard.html", {
        "message": "Hello, World!"
    })
