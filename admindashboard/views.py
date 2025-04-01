from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    # You might want to check here that the logged-in admin is valid (e.g. using session data)
    return render(request, "admindashboard/admin_dashboard.html")

# Create your views here.
