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

# Dashboard
def dashboard_view(request):
    field_workers = UserProfile.objects.filter(role="User").count()
    admins        = UserProfile.objects.filter(role="Admin").count()
    total_users   = field_workers + admins
    logs          = Log.objects.all().order_by('-timestamp')[:5]
    today         = datetime.now()

    # define users for the template loop
    users = UserProfile.objects.filter(is_archived=False)

    return render(request, "dashboardadminapp/dashboard.html", {
        "field_workers": field_workers,
        "admins": admins,
        "total_users": total_users,
        "logs": logs,
        "today": today,
        "users": users,
    })


# List active users
def users_view(request):
    users = UserProfile.objects.filter(is_archived=False)
    context = {
        "users": users,
        "active_users": users.filter(is_active=True).count(),
        "disabled_users": users.filter(is_active=False).count(),
        "admins": users.filter(role="Admin").count(),
        "field_workers": users.filter(role="User").count(),
        "today": datetime.now(),
    }
    return render(request, "dashboardadminapp/users.html", context)

# List archived users
def archived_users(request):
    users = UserProfile.objects.filter(is_archived=True)
    today = datetime.now()
    return render(request, "dashboardadminapp/archived_user.html", {
        "users": users,
        "today": today
    })

# Add new user
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

        # 2. Create UserProfile (custom_user_id is auto-generated after save)
        profile = UserProfile.objects.create(
            user=user,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            role=role,
            last_active=now(),
            is_active=True
        )

        messages.success(request, f"User {profile.custom_user_id} added successfully!")
        return redirect("dashboardadminapp:users")

    return render(request, "dashboardadminapp/add_user.html")


# Edit user
def edit_user(request, user_id):
    profile = get_object_or_404(UserProfile, id=user_id)
    if request.method=="POST":
        profile.first_name = request.POST.get("first_name", profile.first_name)
        profile.last_name  = request.POST.get("last_name", profile.last_name)
        profile.email      = request.POST.get("email", profile.email)
        profile.role       = request.POST.get("role", profile.role)
        profile.save()
        messages.success(request,"User updated successfully!")
        return redirect("dashboardadminapp:users")
    return render(request,"dashboardadminapp/edit_user.html", {"user": profile})

# Archive user (AJAX)
@csrf_exempt
def archive_user(request, user_id):
    # fetch the profile (404 if missing)
    profile = get_object_or_404(UserProfile, id=user_id)

    # mark archived
    profile.is_archived = True
    profile.is_active   = False
    profile.save()

    # if it was an AJAX POST, return JSON
    if request.method == "POST" and request.is_ajax():
        return JsonResponse({"success": True})

    # if it was a normal GET or non-AJAX POST, redirect back to list
    if request.method in ("GET", "POST"):
        return redirect('dashboardadminapp:users')

    # anything else is truly invalid
    return HttpResponseNotAllowed(["GET","POST"])

# Disable user (AJAX)
@csrf_exempt
def disable_user(request, user_id):
    # 1) fetch the profile or 404
    profile = get_object_or_404(UserProfile, id=user_id)
    # 2) toggle off
    profile.is_active = False
    profile.save()

    # detect AJAX via header
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # 3a) if AJAX POST, return JSON success
    if request.method == "POST" and is_ajax:
        return JsonResponse({"success": True})

    # 3b) if normal GET or POST, redirect back to active users list
    if request.method in ("GET", "POST"):
        return redirect('dashboardadminapp:users')

    # 4) anything else: method not allowed
    return HttpResponseNotAllowed(["GET", "POST"])

# Roles page
def roles_view(request):
    # fetch the profiles so your template sees custom_user_id, can_classify, etc.
    profiles = UserProfile.objects.all()
    return render(request, 'dashboardadminapp/roles.html', {
        "users": profiles,
        "today": datetime.now(),
    })

# Assign roles (AJAX)
def assign_roles(request):
    if request.method=="POST":
        data = json.loads(request.body)
        role = data.get("role")
        ids  = data.get("user_ids",[])
        if role:
            UserProfile.objects.filter(id__in=ids).update(role=role)
            return JsonResponse({"success":True})
        return JsonResponse({"success":False,"error":"No role specified"})
    return JsonResponse({"success":False,"error":"Invalid method"})

# Logs page
def logs_view(request):
    return render(request,"dashboardadminapp/logs.html",{"today":datetime.now()})

# Logout
def custom_logout(request):
    logout(request)
    return redirect(reverse('superadminloginapp:login'))

@csrf_exempt
def restore_user(request, user_id):
    profile = get_object_or_404(UserProfile, id=user_id)
    # Always perform the un-archive
    profile.is_archived = False
    profile.is_active   = True
    profile.save()

    # Detect AJAX by header
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if request.method == "POST" and is_ajax:
        return JsonResponse({"success": True})

    if request.method in ("GET", "POST"):
        return redirect('dashboardadminapp:users')

    return HttpResponseNotAllowed(["GET", "POST"])
