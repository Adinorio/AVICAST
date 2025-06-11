from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout, get_user_model
from django.utils.timezone import now
from .models import UserProfile, User, PermissionSetting, SystemLog
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
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

# Get the User model
User = get_user_model()

def check_auth(view_func):
    def wrapper(request, *args, **kwargs):
        logger.info('=' * 50)
        logger.info('check_auth decorator called')
        logger.info(f'User authenticated: {request.user.is_authenticated}')
        logger.info(f'User: {request.user}')
        logger.info(f'Session data: {dict(request.session)}')
        
        if not request.user.is_authenticated:
            logger.warning('User not authenticated, redirecting to login')
            return redirect('authentication:login')
            
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
            return redirect('authentication:login')
    return wrapper

# Dashboard
@check_auth
def dashboard_view(request):
    """Main dashboard view"""
    try:
        # Get all field workers
        field_workers = User.objects.filter(role='field_worker')
        
        # Get all users
        users = User.objects.all()
        
        # Get all roles from the User model
        roles = User._meta.get_field('role').choices
        
        # Get recent logs
        recent_logs = SystemLog.objects.all().order_by('-timestamp')[:5]
        
        context = {
            "field_workers": field_workers,
            "users": users,
            "roles": roles,
            "recent_logs": recent_logs,
        }
        
        return render(request, "user_management/dashboard.html", context)
    except Exception as e:
        logger.error(f"Error in dashboard view: {str(e)}")
        logger.error(traceback.format_exc())
        return HttpResponse(f"Dashboard error: {str(e)}<br><pre>{traceback.format_exc()}</pre>")

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
                custom_user_id=email,
                first_name=first_name,
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

            # Validate required fields
            if not all([first_name, last_name, password, role]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'All fields are required'
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
                role=role
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
                'message': f'User {custom_id} created successfully',
                'user_id': custom_id
            })
        except Exception as e:
            print(f'Error creating user: {e}')
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to create user: {e}'
            }, status=500)

    return HttpResponseNotAllowed(['POST'])


# Edit user
@check_auth
def edit_user(request, user_id=None):
    if request.method == "POST":
        try:
            user_to_edit = get_object_or_404(User, custom_id=user_id)  # Fetch user from User model
            user_profile = get_object_or_404(UserProfile, user=user_to_edit) # Fetch profile from UserProfile

            user_to_edit.first_name = request.POST.get("first_name")
            user_to_edit.last_name = request.POST.get("last_name")
            user_to_edit.email = request.POST.get("email")
            user_to_edit.role = request.POST.get("role")
            
            # Update is_active based on the checkbox value
            user_to_edit.is_active = request.POST.get("is_active") == 'on'

            # Only update password if provided and not empty
            new_password = request.POST.get("password")
            if new_password:
                user_to_edit.set_password(new_password)

            user_to_edit.save()

            user_profile.first_name = user_to_edit.first_name
            user_profile.last_name = user_to_edit.last_name
            user_profile.email = user_to_edit.email
            user_profile.role = user_to_edit.role
            user_profile.last_active = now()
            user_profile.save()

            messages.success(request, f"User {user_to_edit.custom_id} updated successfully!")
            return redirect("dashboardadminapp:users")
        except Exception as e:
            logger.error(f'Error updating user: {str(e)}')
            logger.error(traceback.format_exc())
            messages.error(request, "Error updating user. Please try again.")
            return redirect("dashboardadminapp:edit_user", user_id=user_id)

    else:
        try:
            user = get_object_or_404(User, custom_id=user_id)
            user_profile = get_object_or_404(UserProfile, user=user)
            context = {
                'user': user_profile, # Pass the profile to the template
                'is_active_checked': 'checked' if user.is_active else '',
            }
            return render(request, 'user_management/edit_user.html', context)
        except Exception as e:
            logger.error(f'Error fetching user for edit: {str(e)}')
            logger.error(traceback.format_exc())
            messages.error(request, "User not found.")
            return redirect("dashboardadminapp:users")


@csrf_exempt
@check_auth
def disable_user(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, custom_id=user_id)
            user.is_active = False  # Set user as inactive
            user.save()
            messages.success(request, f"User {user.custom_id} disabled successfully.")
            return JsonResponse({'status': 'success', 'message': 'User disabled'})
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except Exception as e:
            logger.error(f'Error disabling user: {str(e)}')
            logger.error(traceback.format_exc())
            messages.error(request, "Error disabling user.")
            return JsonResponse({'status': 'error', 'message': f'Error: {e}'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@check_auth
def roles_view(request):
    # Get permission settings for admin and field worker
    admin_permissions = PermissionSetting.objects.filter(role='Admin').first()
    field_worker_permissions = PermissionSetting.objects.filter(role='Field Worker').first()

    # If settings don't exist, create default ones
    if not admin_permissions:
        admin_permissions = PermissionSetting.objects.create(role='Admin')
    if not field_worker_permissions:
        field_worker_permissions = PermissionSetting.objects.create(role='Field Worker')

    context = {
        'admin_permissions': admin_permissions,
        'field_worker_permissions': field_worker_permissions,
    }
    return render(request, 'dashboardadminapp/roles.html', context)

@check_auth
def assign_roles(request):
    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, "dashboardadminapp/assign_roles.html", context)

@csrf_exempt
@check_auth
def update_permission(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            permission_id = data.get('permissionId')
            is_checked = data.get('isChecked')
            action = data.get('action')

            permission_setting = get_object_or_404(PermissionSetting, id=permission_id)

            if action == 'user_management':
                permission_setting.can_manage_users = is_checked
            elif action == 'data_management':
                permission_setting.can_manage_data = is_checked
            elif action == 'report_generation':
                permission_setting.can_generate_reports = is_checked
            elif action == 'site_management':
                permission_setting.can_manage_sites = is_checked
            elif action == 'view_logs':
                permission_setting.can_view_logs = is_checked
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

            permission_setting.save()
            return JsonResponse({'status': 'success', 'message': 'Permission updated'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except PermissionSetting.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Permission setting not found'}, status=404)
        except Exception as e:
            logger.error(f"Error updating permission: {e}")
            logger.error(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {e}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def logs_view(request):
    # Get all logs
    logs_list = SystemLog.objects.all().order_by('-timestamp')
    
    paginator = Paginator(logs_list, 10) # Show 10 logs per page
    page_number = request.GET.get('page')
    try:
        logs = paginator.page(page_number)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    return render(request, 'dashboardadminapp/logs.html', {'logs': logs})

@check_auth
def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('authentication:login')


@csrf_exempt
@check_auth
def restore_user(request, user_id):
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, custom_id=user_id)
            user.is_active = True  # Set user as active
            user.save()
            messages.success(request, f"User {user.custom_id} restored successfully.")
            return JsonResponse({'status': 'success', 'message': 'User restored'})
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except Exception as e:
            messages.error(request, "Error restoring user.")
            return JsonResponse({'status': 'error', 'message': f'Error: {e}'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@check_auth
def forgot_password_request(request):
    return render(request, 'user_management/forgot_password_request.html')

@check_auth
def notifications_view(request):
    return render(request, 'dashboardadminapp/notifications.html')

@check_auth
def settings_view(request):
    return render(request, 'user_management/settings.html')

@login_required
def get_user_stats(request):
    # This view seems to be for AJAX stats, not direct user creation or edit
    # It's currently protected by @login_required, which is good.
    total_users_count = User.objects.count()
    admin_count = User.objects.filter(role='admin').count()
    field_worker_count = User.objects.filter(role='field_worker').count()

    # Users created in the last 24 hours
    one_day_ago = timezone.now() - timedelta(hours=24)
    new_users_24h = User.objects.filter(date_created__gte=one_day_ago).count()

    data = {
        'totalUsers': total_users_count,
        'adminCount': admin_count,
        'fieldWorkerCount': field_worker_count,
        'newUsers24h': new_users_24h,
    }
    return JsonResponse(data)

def is_super_admin(user):
    return user.is_authenticated and user.role == 'super_admin'

def is_admin_or_field_worker(user):
    return user.is_authenticated and user.role in ['admin', 'field_worker'] 