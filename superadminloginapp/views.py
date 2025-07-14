from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
from dashboardadminapp.models import User as DashboardUser, SystemLog
from .models import User as SuperAdminUser
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
import logging
import traceback
import sys
from django.contrib import messages

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def login_view(request):
    error_message = None
    logger.info('=' * 50)
    logger.info('Login view called')
    logger.info(f'Request method: {request.method}')
    logger.info(f'Request path: {request.path}')
    logger.info(f'Request GET params: {request.GET}')
    logger.info(f'Request POST params: {request.POST}')
    logger.info(f'Session data: {dict(request.session)}')
    logger.info(f'User authenticated: {request.user.is_authenticated}')

    # Get the next URL from the request
    next_url = request.GET.get('next', 'admindashboard:dashboard')  # Default to admin dashboard

    # If user is already authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        logger.info('User already authenticated, checking role')
        if request.user.role == 'super_admin':
            logger.info('User is super admin, redirecting to super admin dashboard')
            return redirect('dashboardadminapp:dashboard')
        else:
            logger.info('User is admin/field worker, redirecting to admin dashboard')
            return redirect('admindashboard:dashboard')

    if request.method == "POST":
        logger.info('POST request received')
        form = LoginForm(request.POST)
        logger.info(f'Form is valid: {form.is_valid()}')
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']
            logger.info(f'Form data - user_id: {user_id}')

            try:
                # First try to find user in new model by custom_id
                logger.info('Looking for user in new model by custom_id')
                try:
                    new_user = DashboardUser.objects.get(custom_id=user_id)
                    logger.info(f'Found user in new model by custom_id: {new_user.username}, current role: {new_user.role}')
                    if new_user.check_password(password):
                        logger.info('Password check successful with new model')
                        
                        # Ensure user 010101 is always treated as super_admin upon login
                        if user_id == '010101':
                            logger.info(f'Attempting to correct role for user {user_id}. Current role: {new_user.role}, is_superuser: {new_user.is_superuser}')
                            if new_user.role != 'super_admin' or not new_user.is_superuser:
                                new_user.role = 'super_admin'
                                new_user.is_superuser = True
                                logger.info(f'Role corrected to: {new_user.role}, is_superuser: {new_user.is_superuser}')
                        elif not new_user.role: # Existing logic for other users with no role set
                            new_user.role = 'admin'  # Default role if none set
                            new_user.is_superuser = False # Ensure non-super_admin if role was defaulted
                        else: # Ensure is_superuser matches the role for other users
                            new_user.is_superuser = (new_user.role == 'super_admin')
                        
                        new_user.is_active = True
                        new_user.is_staff = True 
                        new_user.save()
                        logger.info(f'User {new_user.username} (ID: {new_user.custom_id}) saved with role: {new_user.role}, is_superuser: {new_user.is_superuser}')
                        
                        # Log in the user
                        login(request, new_user, backend='django.contrib.auth.backends.ModelBackend')
                        logger.info(f'User {new_user.username} logged in successfully')
                        logger.info(f'Session after login: {dict(request.session)}')
                        
                        # Log successful login
                        SystemLog.objects.create(
                            level='INFO',
                            source='system.auth',
                            message=f"User '{new_user.username}' logged in successfully.",
                            user=new_user,
                            action='login'
                        )
                        
                        # Redirect based on role
                        if new_user.role == 'super_admin':
                            logger.info('User is super admin, redirecting to super admin dashboard')
                            return redirect('dashboardadminapp:dashboard')
                        else:
                            logger.info('User is admin/field worker, redirecting to admin dashboard')
                            return redirect('admindashboard:dashboard')
                    else:
                        logger.warning('Invalid password for new model user')
                        error_message = "Invalid password"
                except DashboardUser.DoesNotExist:
                    logger.info('User not found by custom_id, trying username')
                    try:
                        new_user = DashboardUser.objects.get(username=user_id)
                        logger.info(f'Found user in new model by username: {new_user.username}, current role: {new_user.role}')
                        if new_user.check_password(password):
                            logger.info('Password check successful with new model')
                            # Ensure user has correct role
                            if not new_user.role:
                                new_user.role = 'admin'  # Default role if none set
                            new_user.is_active = True
                            new_user.is_staff = True
                            new_user.is_superuser = (new_user.role == 'super_admin')
                            new_user.save()
                            logger.info(f'User {new_user.username} (ID: {new_user.custom_id}) saved with role: {new_user.role}, is_superuser: {new_user.is_superuser}')
                            
                            # Log in the user
                            login(request, new_user, backend='django.contrib.auth.backends.ModelBackend')
                            logger.info(f'User {new_user.username} logged in successfully')
                            logger.info(f'Session after login: {dict(request.session)}')
                            
                            # Log successful login
                            SystemLog.objects.create(
                                level='INFO',
                                source='system.auth',
                                message=f"User '{new_user.username}' logged in successfully.",
                                user=new_user,
                                action='login'
                            )
                            
                            # Redirect based on role
                            if new_user.role == 'super_admin':
                                logger.info('User is super admin, redirecting to super admin dashboard')
                                return redirect('dashboardadminapp:dashboard')
                            else:
                                logger.info('User is admin/field worker, redirecting to admin dashboard')
                                return redirect('admindashboard:dashboard')
                        else:
                            logger.warning('Invalid password for new model user')
                            error_message = "Invalid password"
                    except DashboardUser.DoesNotExist:
                        logger.info('User not found in new model')
                        error_message = "User not found"
            except Exception as e:
                logger.error(f'Unexpected error during login: {str(e)}')
                logger.error(traceback.format_exc())
                error_message = "An error occurred during login"
        else:
            logger.warning(f'Form validation failed: {form.errors}')
            error_message = "Invalid form data"
    else:
        logger.info('GET request received')
        form = LoginForm()

    logger.info(f'Rendering login template with error: {error_message}')
    logger.info('=' * 50)
    return render(request, 'superadminloginapp/login.html', {
        'form': form, 
        'error_message': error_message,
        'next': next_url
    })

@login_required
def logout_view(request):
    user = request.user if request.user.is_authenticated else None
    if user:
        SystemLog.objects.create(
            level='INFO',
            source='system.auth',
            message=f"User '{user.username}' logged out.",
            user=user,
            action='logout'
        )
    logout(request)
    return redirect('superadminloginapp:login')