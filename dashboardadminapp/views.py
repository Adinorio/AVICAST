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
from django.db.models import Max
from django.contrib.auth.hashers import make_password

def dashboard_view(request):
    field_workers = UserProfile.objects.filter(role="User").count()
    admins = UserProfile.objects.filter(role="Admin").count()
    total_users = field_workers + admins
    logs = Log.objects.all().order_by('-timestamp')[:5]

    return render(request, "dashboardadminapp/dashboard.html", {
        "field_workers": field_workers,
        "admins": admins,
        "total_users": total_users,
        "logs": logs
    })

def users_view(request):
    users = UserProfile.objects.all()
    active_users = users.filter(is_active=True).count()
    disabled_users = users.filter(is_active=False).count()

    return render(request, "dashboardadminapp/users.html", {
        "users": users,
        "active_users": active_users,
        "disabled_users": disabled_users,
    })

def generate_user_id():
    last_user = UserProfile.objects.aggregate(Max('id'))["id__max"] or 0
    new_id = last_user + 1
    return f"25-2409-{new_id:03d}"

def add_user(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if User.objects.filter(user_id=email).exists():
            messages.error(request, "A user with this ID already exists.")
            return redirect("dashboardadminapp:add_user")

        # Create User with hashed password
        user = User.objects.create(
            user_id=email, 
            password=make_password(password)
        )

        # Create UserProfile linked to User
        UserProfile.objects.create(
            user=user,
            custom_user_id=generate_user_id(),
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            last_active=now(),
            is_active=True
        )

        messages.success(request, "User added successfully!")
        return redirect("dashboardadminapp:users")

    return render(request, "dashboardadminapp/add_user.html")

def roles_view(request):
    users = UserProfile.objects.filter(is_active=True)
    return render(request, 'dashboardadminapp/roles.html', {'users': users})

def logs_view(request):
    return render(request, "dashboardadminapp/logs.html")

def custom_logout(request):
    logout(request)
    return redirect('/superadmin/login/')

@csrf_exempt
def archive_user(request, user_id):
    if request.method == "POST":
        try:
            user_profile = get_object_or_404(UserProfile, id=user_id)
            user_profile.is_archived = True  # Correct model
            user_profile.is_active = False
            user_profile.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method."})

def archived_users(request):
    users = UserProfile.objects.filter(is_archived=True)
    return render(request, 'dashboardadminapp/archived_users.html', {'users': users})

def edit_user(request, user_id):
    user_profile = get_object_or_404(UserProfile, id=user_id)  
    user = user_profile.user  # Get related auth user

    if request.method == "POST":
        first_name = request.POST.get("first_name", user_profile.first_name)
        last_name = request.POST.get("last_name", user_profile.last_name)
        email = request.POST.get("email", user_profile.email)
        role = request.POST.get("role", user_profile.role)

        # Update both User and UserProfile
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        user_profile.first_name = first_name
        user_profile.last_name = last_name
        user_profile.email = email
        user_profile.role = role
        user_profile.save()

        messages.success(request, "User updated successfully!")
        return redirect('dashboardadminapp:users')

    return render(request, 'dashboardadminapp/edit_user.html', {'user': user_profile})

def assign_roles(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_ids = data.get("user_ids", [])
            role = data.get("role")  # Expecting a single role

            if not role:
                return JsonResponse({"success": False, "error": "No role specified."})
            #Test
            # Update users' roles
            UserProfile.objects.filter(id__in=user_ids).update(role=role)

            return JsonResponse({"success": True, "message": "Roles updated successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})
