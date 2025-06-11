from functools import wraps
from django.shortcuts import redirect, render
from src.apps.user_management.models import PermissionSetting, User

def permission_required(permission_key):
    # Mapping of permission keys to user-friendly feature names
    FEATURE_NAMES = {
        'view_report_management': 'Report Management',
        'generate_reports': 'Generating Reports',
        'view_species_management': 'Species Management',
        'modify_data': 'Modifying Data',
        'view_site_management': 'Site Management',
        'add_sites': 'Adding Sites',
        'view_bird_census_management': 'Bird Census Management',
        'add_birds': 'Adding Birds',
        'view_image_processing': 'Image Processing',
        'generate_data': 'Generating Image Data',
    }

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login') # Redirect to login if not authenticated
            
            user_role = request.user.role # Assuming user has a 'role' attribute

            # For super_admin, always allow access to specific features without overlay
            if user_role == 'super_admin':
                return view_func(request, *args, **kwargs)

            try:
                # Get the permission settings for the user's role
                permission_setting = PermissionSetting.objects.get(role=user_role)
                
                # Check if the specific permission is True
                if hasattr(permission_setting, permission_key) and getattr(permission_setting, permission_key):
                    # Permission granted, execute the view normally
                    return view_func(request, *args, **kwargs)
                else:
                    # Permission denied for non-super_admin - set context variables
                    request.access_denied = True
                    request.denied_feature_name = FEATURE_NAMES.get(permission_key, 'this feature')
                    return view_func(request, *args, **kwargs) # Continue to render the page
            except PermissionSetting.DoesNotExist:
                # No permission settings for role, deny access via context
                request.access_denied = True
                request.denied_feature_name = FEATURE_NAMES.get(permission_key, 'this feature')
                return view_func(request, *args, **kwargs) # Continue to render the page
            except Exception as e:
                # Log the error for debugging
                print(f"Error in permission_required decorator: {e}")
                request.access_denied = True
                request.denied_feature_name = 'this feature (due to an error)'
                return view_func(request, *args, **kwargs) # Continue to render the page

        return _wrapped_view
    return decorator 