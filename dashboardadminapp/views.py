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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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