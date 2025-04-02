# views.py
from django.shortcuts import render, redirect
from dashboardadminapp.models import UserProfile
from django.contrib.auth import logout

# Simple dashboard view without login required
def dashboard_view(request):
    return render(request, "admindashboard/dashboard.html")

def logout_view(request):
    logout(request)  # Logout the user
    return redirect('superadminloginapp:login')  # Redirect to login page
