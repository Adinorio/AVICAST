from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import User
from dashboardadminapp.models import UserProfile
from .forms import LoginForm
from django.contrib.auth import logout

def login_view(request):
    error_message = None

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']

            # Superadmin check (user_id = "010101")
            if user_id == "010101":
                try:
                    superadmin = User.objects.get(user_id=user_id)
                    if check_password(password, superadmin.password):
                        # Store user_id and custom_user_id in session
                        request.session['user_id'] = superadmin.user_id  # Store superadmin's user_id
                        return redirect("dashboardadminapp:dashboard")  # Superadmin Dashboard
                    else:
                        error_message = "Invalid password"
                except User.DoesNotExist:
                    error_message = "Superadmin user not found"

            else:
                # Check if user_id is a custom_user_id in UserProfile (for regular admins)
                try:
                    user_profile = UserProfile.objects.get(custom_user_id=user_id)
                    if check_password(password, user_profile.user.password):  # Authenticate against User model
                        # Store custom_user_id in session
                        request.session['user_id'] = user_profile.custom_user_id  # Store user's custom_user_id
                        return redirect("admindashboard:dashboard")  # Admin Dashboard
                    else:
                        error_message = "Invalid password"
                except UserProfile.DoesNotExist:
                    error_message = "User not found"

    else:
        form = LoginForm()

    # Render the login page with the form and possible error message
    return render(request, "superadminloginapp/login.html", {"form": form, "error_message": error_message})

def logout_view(request):
    logout(request)  # This logs out the user
    return redirect('/accounts/login/')