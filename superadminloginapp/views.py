from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password, make_password
from dashboardadminapp.models import User as DashboardUser
from .models import User as SuperAdminUser
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
import logging
import traceback
import sys

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
    next_url = request.GET.get('next', 'dashboardadminapp:dashboard')

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
                # First try to find user in new model
                logger.info('Looking for user in new model')
                try:
                    new_user = DashboardUser.objects.get(username=user_id)
                    logger.info('Found user in new model')
                    if new_user.check_password(password):
                        logger.info('Password check successful with new model')
                        # Ensure user has correct role
                        if not new_user.role:
                            new_user.role = 'admin'  # Default role if none set
                        new_user.is_active = True
                        new_user.is_staff = True
                        new_user.is_superuser = (new_user.role == 'super_admin')
                        new_user.save()
                        
                        # Log in the user
                        login(request, new_user, backend='django.contrib.auth.backends.ModelBackend')
                        logger.info(f'User {new_user.username} logged in successfully')
                        logger.info(f'Session after login: {dict(request.session)}')
                        
                        # Redirect based on role and next parameter
                        if next_url:
                            logger.info(f'Redirecting to next URL: {next_url}')
                            return redirect(next_url)
                        elif new_user.role == 'super_admin':
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
                
                # If new model fails, try old model
                logger.info('Trying old model')
                try:
                    old_user = SuperAdminUser.objects.get(user_id=user_id)
                    logger.info(f'Found old user: {old_user.user_id}')
                    
                    if check_password(password, old_user.password):
                        logger.info('Password check successful with old model')
                        try:
                            # Create or update user in new model
                            new_user, created = DashboardUser.objects.get_or_create(
                                username=user_id,
                                defaults={
                                    'custom_id': user_id,
                                    'role': 'admin',  # Default to admin role for old users
                                    'is_active': True,
                                    'is_staff': True,
                                    'is_superuser': False
                                }
                            )
                            
                            if not created:
                                logger.info('Updating existing user in new model')
                                new_user.role = 'admin'  # Default to admin role for old users
                                new_user.is_active = True
                                new_user.is_staff = True
                                new_user.is_superuser = False
                            
                            # Set the password using the proper method
                            new_user.set_password(password)
                            new_user.save()
                            
                            # Log in the user
                            login(request, new_user, backend='django.contrib.auth.backends.ModelBackend')
                            logger.info(f'User {new_user.username} logged in successfully')
                            logger.info(f'Session after login: {dict(request.session)}')
                            
                            # Redirect based on next parameter
                            if next_url:
                                logger.info(f'Redirecting to next URL: {next_url}')
                                return redirect(next_url)
                            else:
                                logger.info('User is from old model, redirecting to admin dashboard')
                                return redirect('admindashboard:dashboard')
                        except Exception as create_error:
                            logger.error(f'Error creating/updating user: {str(create_error)}')
                            logger.error(traceback.format_exc())
                            error_message = "Error creating user account"
                    else:
                        logger.warning(f'Invalid password for user {user_id}')
                        error_message = "Invalid password"
                except SuperAdminUser.DoesNotExist:
                    logger.warning(f'User not found: {user_id}')
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
    logger.info('Logout view called')
    logger.info(f'User {request.user.username} logging out')
    
    # Clear the session
    request.session.flush()
    
    # Log out the user
    logout(request)
    
    logger.info('User logged out successfully')
    return redirect('superadminloginapp:login')