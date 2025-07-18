from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.utils.timezone import now
from .models import UserProfile, User, PermissionSetting, SystemLog
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib.auth.hashers import make_password
from datetime import datetime
from django.http import JsonResponse, HttpResponseNotAllowed
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import traceback
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models

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
            # Only allow super_admin role
            if hasattr(request.user, 'role') and request.user.role == 'super_admin':
                logger.info('User is super admin')
                return view_func(request, *args, **kwargs)
            
            # Redirect all other roles to admin dashboard
            logger.warning('User is not super admin, redirecting to admin dashboard')
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
        today = datetime.now()
        logs = SystemLog.objects.all().order_by('-timestamp')[:5]
        recent_logs = SystemLog.objects.filter(action__in=['login', 'logout']).order_by('-timestamp')[:5]

        return render(request, "dashboardadminapp/dashboard.html", {
            "field_workers": field_workers,
            "admins": admins,
            "total_users": total_users,
            "today": today,
            "logs": logs,
            "recent_logs": recent_logs,
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
    users_list = User.objects.all().order_by('-date_created')  # Sort by newest created to oldest
    
    paginator = Paginator(users_list, 5) # Show 5 users per page
    page_number = request.GET.get('page')
    try:
        users = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        users = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        users = paginator.page(paginator.num_pages)

    total_users = users_list.count()
    daily_active_users = users_list.filter(date_created__gte=timezone.now() - timedelta(days=1)).count()
    latest_user_id = users_list.order_by('-date_created').first().custom_id if users_list.exists() else 'N/A'

    logger.info(f"Number of users on current page (from paginator): {users.object_list.count()}")
    
    context = {
        'users': users,
        'total_users': total_users,
        'daily_active_users': daily_active_users,
        'latest_user_id': latest_user_id,
        'num_pages': paginator.num_pages,
        'current_page_number': users.number,
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

# Create user (re-added)
@login_required
def create_user(request):
    if request.method == 'POST':
        try:
            # Get data from POST request
            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            password = request.POST.get('password')
            role = request.POST.get('role')
            custom_id = request.POST.get('customId')  # Get custom ID if provided

            # Validate required fields
            if not all([first_name, last_name, password, role]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All fields are required'
                }, status=400)

            # For super_admin role, validate custom ID
            if role == 'super_admin':
                if not custom_id or not custom_id.isdigit() or len(custom_id) != 6:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Super Admin requires a valid 6-digit custom ID'
                    }, status=400)
                
                # Check if custom ID already exists
                if User.objects.filter(custom_id=custom_id).exists():
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Custom ID {custom_id} is already in use'
                    }, status=400)

            # Check for existing user with same name
            existing_user = User.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            ).first()

            if existing_user:
                return JsonResponse({
                    'status': 'error',
                    'message': f'A user with the name {first_name} {last_name} already exists'
                }, status=400)

            # Generate custom ID for non-super_admin users
            if role != 'super_admin':
                # Get the latest user ID and increment
                latest_user = User.objects.order_by('-custom_id').first()
                if latest_user and latest_user.custom_id:
                    # Extract the sequence number and increment
                    sequence = int(latest_user.custom_id.split('-')[-1]) + 1
                else:
                    sequence = 1

                # Format: YY-MMDD-XXX
                today = datetime.now()
                year = str(today.year)[-2:]
                month = str(today.month).zfill(2)
                day = str(today.day).zfill(2)
                custom_id = f"{year}-{month}{day}-{str(sequence).zfill(3)}"

            # Create the user
            user = User.objects.create(
                username=custom_id,
                first_name=first_name,
                last_name=last_name,
                custom_id=custom_id,
                role=role,
                is_active=True,
                is_staff=True,
                is_superuser=(role == 'super_admin')
            )
            user.set_password(password)
            user.save()

            # Create the user profile
            profile = UserProfile.objects.create(
                user=user,
                custom_user_id=custom_id,
                first_name=first_name,
                last_name=last_name,
                email=f"{custom_id}@example.com",  # Generate a unique email
                role=role
            )

            return JsonResponse({
                'status': 'success',
                'message': 'User created successfully',
                'user_id': custom_id
            })

        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error creating user: {str(e)}'
            }, status=500)

    return render(request, 'dashboardadminapp/create_user.html')

# Edit user
@check_auth
def edit_user(request, user_id=None):
    # Fetch user details for GET request to populate form
    if request.method == 'GET':
        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'User ID is required for GET request'}, status=400)
        user = get_object_or_404(User, custom_id=user_id)
        return JsonResponse({
            'custom_id': user.custom_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
        })

    # Handle POST request for updating user
    if request.method == 'POST':
        try:
            # Retrieve the user object for update using user_id from POST data
            user_id_from_post = request.POST.get('user_id')
            logger.info(f"Edit user POST request received for user_id: {user_id_from_post}")
            user_to_update = get_object_or_404(User, custom_id=user_id_from_post)
            logger.info(f"User object retrieved: {user_to_update.username}")

            first_name = request.POST.get('firstName')
            last_name = request.POST.get('lastName')
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirmPassword')
            role = request.POST.get('role')
            logger.info(f"Received data: First Name='{first_name}', Last Name='{last_name}', Role='{role}', Password provided={bool(password)}")

            # Validate required fields (excluding password for optional update)
            if not all([first_name, last_name, role]):
                logger.warning("Missing required fields for user update.")
                return JsonResponse({
                    'status': 'error',
                    'message': 'First name, Last name, and Role are required'
                }, status=400)

            # Check for duplicate name, excluding the current user
            existing_user = User.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            ).exclude(custom_id=user_id_from_post).first()

            if existing_user:
                logger.warning(f"Duplicate name detected for user {first_name} {last_name}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'A user with the name {first_name} {last_name} already exists'
                }, status=400)
            
            logger.info(f"User object before update: First Name='{user_to_update.first_name}', Last Name='{user_to_update.last_name}', Role='{user_to_update.role}'")
            user_to_update.first_name = first_name
            user_to_update.last_name = last_name
            user_to_update.role = role
            logger.info(f"User object after assignment: First Name='{user_to_update.first_name}', Last Name='{user_to_update.last_name}', Role='{user_to_update.role}'")

            # Update password only if provided and matches
            if password and confirm_password:
                if password != confirm_password:
                    logger.warning("Passwords do not match for update.")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Passwords do not match'
                    }, status=400)
                user_to_update.set_password(password)
                logger.info("User password updated.")
            elif (password and not confirm_password) or (not password and confirm_password):
                logger.warning("Only one password field provided for update.")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Both password fields must be filled if updating password'
                }, status=400)

            user_to_update.save()
            logger.info("User object saved successfully.")

            # Update corresponding UserProfile (optional, depending on your data model split)
            if hasattr(user_to_update, 'profile'):
                user_to_update.profile.first_name = first_name
                user_to_update.profile.last_name = last_name
                user_to_update.profile.role = role
                user_to_update.profile.save()
                logger.info("User profile saved successfully.")

            return JsonResponse({
                'status': 'success',
                'message': 'User updated successfully',
                'user_id': user_to_update.custom_id
            })

        except User.DoesNotExist:
            logger.error(f"User with custom_id {user_id_from_post} not found during update.")
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except Exception as e:
            logger.error(f"Error updating user {user_id_from_post}: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'status': 'error',
                'message': f'Error updating user: {str(e)}'
            }, status=500)

    # For GET requests to edit_user, the user object is already retrieved from the URL parameter
    return HttpResponseNotAllowed(['GET', 'POST'])

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
    # Get permission settings for admin and field worker
    admin_permissions_obj = PermissionSetting.objects.get_or_create(role='admin')[0]
    field_worker_permissions_obj = PermissionSetting.objects.get_or_create(role='field_worker')[0]

    # Convert permission objects to dictionaries for JSON serialization
    admin_permissions = {
        field.name: getattr(admin_permissions_obj, field.name) 
        for field in admin_permissions_obj._meta.fields 
        if isinstance(field, models.BooleanField)
    }
    field_worker_permissions = {
        field.name: getattr(field_worker_permissions_obj, field.name) 
        for field in field_worker_permissions_obj._meta.fields 
        if isinstance(field, models.BooleanField)
    }

    # Get counts of users per role
    num_admins = User.objects.filter(role='admin').count()
    num_field_workers = User.objects.filter(role='field_worker').count()

    context = {
        'admin_permissions': admin_permissions,
        'field_worker_permissions': field_worker_permissions,
        'num_admins': num_admins,
        'num_field_workers': num_field_workers,
    }
    return render(request, 'dashboardadminapp/roles.html', context)

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

# Update individual permission (AJAX)
@csrf_exempt
@check_auth
def update_permission(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            role = data.get('role')
            permission_key = data.get('permission_key')
            is_checked = data.get('is_checked')

            logger.info(f"Received update request: Role={role}, Key={permission_key}, Checked={is_checked}, Type of is_checked={type(is_checked)}")

            if not all([role, permission_key is not None, is_checked is not None]):
                logger.warning("Missing data in update_permission request.")
                return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

            # Ensure the role is valid and the permission key exists in the model
            if role not in ['admin', 'field_worker'] or not hasattr(PermissionSetting, permission_key):
                logger.warning(f"Invalid role ({role}) or permission key ({permission_key}).")
                return JsonResponse({'status': 'error', 'message': 'Invalid role or permission key'}, status=400)

            permission_setting = PermissionSetting.objects.get(role=role)
            setattr(permission_setting, permission_key, bool(is_checked)) # Ensure boolean conversion
            permission_setting.save()

            logger.info(f"Permission updated: Role='{role}', Key='{permission_key}', Value='{is_checked}'")
            return JsonResponse({'status': 'success', 'message': 'Permission updated successfully'})

        except PermissionSetting.DoesNotExist:
            logger.error(f"Permission setting for role '{role}' not found.")
            return JsonResponse({'status': 'error', 'message': f'Permission setting for role {role} not found'}, status=404)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body.")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error updating permission: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'},
                                status=500)
    return HttpResponseNotAllowed(['POST'])

# Logs page
@login_required
def logs_view(request):
    # Get all logs
    logs = SystemLog.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        logs = logs.filter(
            Q(message__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(source__icontains=search_query)
        )
    
    # Filter by level if provided
    level_filter = request.GET.get('level', '')
    if level_filter:
        logs = logs.filter(level=level_filter)
    
    # Pagination
    paginator = Paginator(logs, 5)  # Show 5 logs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get counts for stats
    total_logs = SystemLog.objects.count()
    critical_logs = SystemLog.objects.filter(level='ERROR').count()
    
    context = {
        'logs': page_obj,
        'total_logs': total_logs,
        'critical_logs': critical_logs,
        'current_page': page_number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    }
    
    return render(request, 'dashboardadminapp/logs.html', context)

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

        return JsonResponse({"success": True})
    return HttpResponseNotAllowed(["POST"])

@check_auth
def notifications_view(request):
    return render(request, "dashboardadminapp/notifications.html")

@check_auth
def settings_view(request):
    return render(request, "dashboardadminapp/settings.html")

@login_required
def get_user_stats(request):
    # This view seems to be for AJAX stats, not direct user creation or edit
    # It's currently protected by @login_required, which is good.
    total_users = User.objects.count()
    latest_user = User.objects.order_by('-date_created').first()
    latest_user_id = latest_user.custom_id if latest_user else 'N/A'
    daily_active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=1)).count()
    
    return JsonResponse({
        'total_users': total_users,
        'latest_user_id': latest_user_id,
        'daily_active_users': daily_active_users
    })

# Helper to determine if the user is a super admin for user_passes_test
def is_super_admin(user):
    return user.is_authenticated and user.role == 'super_admin'