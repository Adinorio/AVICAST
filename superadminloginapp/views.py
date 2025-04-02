from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import User
from dashboardadminapp.models import UserProfile
from .forms import LoginForm

def login_view(request):
    error_message = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']

            # Check if user_id belongs to the superadmin
            try:
                user = User.objects.get(user_id=user_id)
                if check_password(password, user.password):
                    return redirect("dashboardadminapp:dashboard")
            except User.DoesNotExist:
                pass  # Continue checking UserProfile

            # Check if user_id is a custom_user_id in UserProfile
            try:
                user_profile = UserProfile.objects.get(custom_user_id=user_id)
                if check_password(password, user_profile.user.password):  # Authenticate against User model
                    return redirect("dashboardadminapp:dashboard")
                else:
                    error_message = "Invalid password"
            except UserProfile.DoesNotExist:
                error_message = "User not found"

    else:
        form = LoginForm()

    return render(request, "superadminloginapp/login.html", {"form": form, "error_message": error_message})
