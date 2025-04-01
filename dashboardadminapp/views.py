from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.utils.timezone import now
from .models import Log, UserProfile
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def dashboard_view(request):
    field_workers = UserProfile.objects.filter(role="User").count()  # Count Users with "User" role
    admins = UserProfile.objects.filter(role="Admin").count()  # Count Users with "Admin" role
    total_users = field_workers + admins  # Total Users = Field Workers + Admins

    logs = Log.objects.all().order_by('-timestamp')[:5]  # Last 5 logs

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

def add_user(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # Ensure email is unique
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("dashboardadminapp:add_user")

        # Create a new User
        user = User.objects.create_user(
            username=email, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        
        # Create UserProfile and associate it with the User
        UserProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            last_active=now(),
            is_active=True
        )

        messages.success(request, "User added successfully!")
        return redirect("dashboardadminapp:users")  # Redirect back to Users page
    
    return render(request, "dashboardadminapp/add_user.html")

def roles_view(request):
    users = UserProfile.objects.filter(is_active=True)  # Fetch only active users
    return render(request, 'dashboardadminapp/roles.html', {'users': users})

def logs_view(request):
    return render(request, "dashboardadminapp/logs.html")

def custom_logout(request):
    logout(request)
    return redirect('/superadmin/login/')  # Redirect to SuperAdmin login page

@csrf_exempt
def archive_user(request, user_id):
    if request.method == "POST":
        try:
            user = User.objects.get(id=user_id)
            user.is_archived = True  # Assuming you have an `is_archived` field in your User model
            user.save()
            return JsonResponse({"success": True})
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "User not found."})
    return JsonResponse({"success": False, "error": "Invalid request method."})

def archived_users(request):
    users = UserProfile.objects.filter(is_archived=True)  # ✅ Query works now
    return render(request, 'dashboardadminapp/archived_users.html', {'users': users})

def edit_user(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)  

    if request.method == "POST":
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.role = request.POST.get("role", user.role)
        user.save()
        messages.success(request, "User updated successfully!")
        return redirect('dashboardadminapp:users')

    return render(request, 'dashboardadminapp/edit_user.html', {'user': user})

def assign_roles(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_ids = data.get("user_ids", [])
            roles = data.get("roles", [])
            assignments = data.get("assignments", [])

            # Update each selected user's roles & assignments
            for user_id in user_ids:
                user = UserProfile.objects.get(id=user_id)
                user.role = roles[0] if roles else user.role  # Assign first selected role
                user.assignments = ", ".join(assignments) if assignments else user.assignments
                user.save()

            return JsonResponse({"success": True, "message": "Roles & assignments updated successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})