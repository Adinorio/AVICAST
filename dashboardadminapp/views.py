from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.utils.timezone import now
from .models import Log, UserProfile, User
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import logging
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import traceback

logger = logging.getLogger(__name__)

def check_auth(view_func):
    def wrapper(request, *args, **kwargs):
        logger.info('=' * 50)
        logger.info('check_auth decorator called')
        logger.info(f'User authenticated: {request.user.is_authenticated}')
        logger.info(f'User: {request.user}')
        logger.info(f'Session data: {dict(request.session)}')
        
        if not request.user.is_authenticated:
            logger.warning('User not authenticated, redirecting to login')
            return redirect('superadminloginapp:login')
            
        try:
            # Check if it's a superadmin
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                logger.info('User is super admin')
                return view_func(request, *args, **kwargs)
            # Check if it's a regular admin
            if hasattr(request.user, 'role') and request.user.role == 'admin':
                logger.info('User is admin')
                return view_func(request, *args, **kwargs)
            logger.warning('User is not admin or super admin, redirecting to admin dashboard')
            return redirect('admindashboard:dashboard')
        except Exception as e:
            logger.error(f'Error in check_auth: {str(e)}')
            logger.error(traceback.format_exc())
            return redirect('superadminloginapp:login')
    return wrapper

# Dashboard
@check_auth
def dashboard_view(request):
    logger.info('=' * 50)
    logger.info('Dashboard view called')
    logger.info(f'User authenticated: {request.user.is_authenticated}')
    logger.info(f'User: {request.user}')
    logger.info(f'Session data: {dict(request.session)}')
    
    try:
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
    except Exception as e:
        logger.error(f'Error in dashboard view: {str(e)}')
        logger.error(traceback.format_exc())
        return redirect('superadminloginapp:login')

def is_super_admin(user):
    return user.is_authenticated and user.role == 'super_admin'

def is_admin_or_field_worker(user):
    return user.is_authenticated and user.role in ['admin', 'field_worker']

# List users
@check_auth
def users_view(request):
    users = User.objects.all()
    total_users = users.count()
    daily_active_users = users.filter(date_created__gte=timezone.now() - timedelta(days=1)).count()
    latest_user_id = users.order_by('-date_created').first().custom_id if users.exists() else 'N/A'
    
    context = {
        'users': users,
        'total_users': total_users,
        'daily_active_users': daily_active_users,
        'latest_user_id': latest_user_id,
    }
    return render(request, 'dashboardadminapp/users.html', context)

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

        # Check if user already exists
        if User.objects.filter(username=email).exists():
            messages.error(request, "A user with this ID already exists.")
            return redirect("dashboardadminapp:add_user")

        try:
            # Create User with proper fields
            user = User.objects.create(
                username=email,  # Use email as username
                custom_id=email,  # Use email as custom_id
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role,
                is_active=True,
                is_staff=True,
                is_superuser=(role == 'super_admin')
            )
            user.set_password(password)  # Properly hash the password
            user.save()

            # Create UserProfile
            profile = UserProfile.objects.create(
                user=user,
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                email=email,
                role=role,
                last_active=now()
            )

            messages.success(request, f"User {user.custom_id} added successfully!")
            return redirect("dashboardadminapp:users")
        except Exception as e:
            logger.error(f'Error creating user: {str(e)}')
            logger.error(traceback.format_exc())
            messages.error(request, "Error creating user. Please try again.")
            return redirect("dashboardadminapp:add_user")

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

@ensure_csrf_cookie
@require_http_methods(["POST"])
@login_required
@user_passes_test(is_super_admin)
def create_user(request):
    logger.info('Create user request received')
    
    # Check if it's an AJAX request
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logger.warning('Non-AJAX request received')
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=400)

    try:
        data = json.loads(request.body)
        logger.info(f'Form data: {data}')
        
        # Extract user data
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'field_worker')
        
        # Validate required fields
        if not all([first_name, last_name, email, password]):
            return JsonResponse({
                'status': 'error',
                'message': 'All fields are required'
            }, status=400)
        
        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'User with this email already exists'
            }, status=400)
        
        # Create the user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True
        )
        
        # Create the user profile
        profile = UserProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            last_active=now()
        )
        
        logger.info(f'User created successfully: {user.username}')
        
        return JsonResponse({
            'status': 'success',
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'custom_id': user.custom_id
            }
        })
        
    except Exception as e:
        logger.error(f'Error creating user: {str(e)}')
        logger.error(traceback.format_exc())
        return JsonResponse({
            'status': 'error',
            'message': f'Error creating user: {str(e)}'
        }, status=500)

@login_required
@user_passes_test(is_super_admin)
def get_user_stats(request):
    total_users = User.objects.count()
    daily_active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=1)).count()
    latest_user_id = User.objects.order_by('-date_created').first().custom_id if User.objects.exists() else 'N/A'
    
    return JsonResponse({
        'total_users': total_users,
        'daily_active_users': daily_active_users,
        'latest_user_id': latest_user_id
    })