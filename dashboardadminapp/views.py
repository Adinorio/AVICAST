from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from superadminloginapp.models import User
from django.contrib.auth import logout
from django.utils.timezone import now
from .models import Log, UserProfile
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.http import JsonResponse, HttpResponseNotAllowed

def check_auth(view_func):
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('superadminloginapp:login')
        try:
            # Check if it's a superadmin
            if request.session['user_id'] == "010101":
                return view_func(request, *args, **kwargs)
            # Check if it's a regular admin
            user_profile = UserProfile.objects.get(custom_user_id=request.session['user_id'])
            if user_profile.role == "Admin":
                return view_func(request, *args, **kwargs)
            return redirect('admindashboard:dashboard')
        except UserProfile.DoesNotExist:
            return redirect('superadminloginapp:login')
    return wrapper

# Dashboard
@check_auth
def dashboard_view(request):
    field_workers = UserProfile.objects.filter(role="User").count()
    admins = UserProfile.objects.filter(role="Admin").count()
    total_users = field_workers + admins
    logs = Log.objects.all().order_by('-timestamp')[:5]
    today = datetime.now()

    return render(request, "dashboardadminapp/dashboard.html", {
        "field_workers": field_workers,
        "admins": admins,
        "total_users": total_users,
        "logs": logs,
        "today": today,
    })

# List users
@check_auth
def users_view(request):
    users = UserProfile.objects.all()
    
    context = {
        "users": users,
        "total_users": users.count(),
        "admins": users.filter(role="Admin").count(),
        "field_workers": users.filter(role="User").count(),
        "today": datetime.now(),
    }
    
    return render(request, "dashboardadminapp/users.html", context)

# List archived users
@check_auth
def archived_users(request):
    users = UserProfile.objects.all()  # Temporarily show all users
    today = datetime.now()
    return render(request, "dashboardadminapp/archived_user.html", {
        "users": users,
        "today": today
    })

# Add new user
@check_auth
def add_user(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        middle_name = request.POST.get("middle_name", "")  # optional field
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if User.objects.filter(user_id=email).exists():
            messages.error(request, "A user with this ID already exists.")
            return redirect("dashboardadminapp:add_user")

        # 1. Create User
        user = User.objects.create(
            user_id=email,
            password=make_password(password)
        )

        # 2. Create UserProfile
        profile = UserProfile.objects.create(
            user=user,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            role=role,
            last_active=now()
        )

        messages.success(request, f"User {profile.custom_user_id} added successfully!")
        return redirect("dashboardadminapp:users")

    return render(request, "dashboardadminapp/add_user.html")

# Edit user
@check_auth
def edit_user(request, user_id):
    profile = get_object_or_404(UserProfile, id=user_id)
    if request.method=="POST":
        profile.first_name = request.POST.get("first_name", profile.first_name)
        profile.last_name = request.POST.get("last_name", profile.last_name)
        profile.email = request.POST.get("email", profile.email)
        profile.role = request.POST.get("role", profile.role)
        profile.save()
        messages.success(request,"User updated successfully!")
        return redirect("dashboardadminapp:users")
    return render(request,"dashboardadminapp/edit_user.html", {"user": profile})

# Disable user (AJAX)
@csrf_exempt
@check_auth
def disable_user(request, user_id):
    profile = get_object_or_404(UserProfile, id=user_id)
    # Temporarily just redirect back
    return redirect('dashboardadminapp:users')

# Roles page
@check_auth
def roles_view(request):
    profiles = UserProfile.objects.all()
    users_count = profiles.count()
    return render(request, 'dashboardadminapp/roles.html', {
        "users": profiles,
        "today": datetime.now(),
        "users_count": users_count,
    })

# Assign roles (AJAX)
@check_auth
def assign_roles(request):
    if request.method=="POST":
        data = json.loads(request.body)
        role = data.get("role")
        ids = data.get("user_ids",[])
        if role:
            UserProfile.objects.filter(id__in=ids).update(role=role)
            return JsonResponse({"success":True})
        return JsonResponse({"success":False,"error":"No role specified"})
    return JsonResponse({"success":False,"error":"Invalid method"})

# Logs page
@check_auth
def logs_view(request):
    return render(request,"dashboardadminapp/logs.html",{"today":datetime.now()})

# Logout
@check_auth
def custom_logout(request):
    logout(request)
    return redirect(reverse('superadminloginapp:login'))

@csrf_exempt
@check_auth
def restore_user(request, user_id):
    profile = get_object_or_404(UserProfile, id=user_id)
    return redirect('dashboardadminapp:users')

@check_auth
def forgot_password_request(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", "").strip()
        try:
            profile = UserProfile.objects.get(custom_user_id=user_id)
        except UserProfile.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown user ID."}, status=404)

        Log.objects.create(
            event=f"{profile.first_name} {profile.last_name} is requesting a change of password."
        )

        return JsonResponse({"success": True})
    return HttpResponseNotAllowed(["POST"])

@check_auth
def notifications_view(request):
    logs = Log.objects.all().order_by('-timestamp')
    return render(request, "dashboardadminapp/notifications.html", {
        "logs": logs,
    })

@check_auth
def settings_view(request):
    return render(request, "dashboardadminapp/settings.html")