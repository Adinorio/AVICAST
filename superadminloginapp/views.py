from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from .models import User
from .forms import LoginForm

def login_view(request):
    error_message = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']

            try:
                user = User.objects.get(user_id=user_id)
                if check_password(password, user.password):
                    # Redirect to dashboard in dashboardadminapp
                    return redirect("dashboardadminapp:dashboard")
                else:
                    error_message = "Invalid password"
            except User.DoesNotExist:
                error_message = "User not found"

    else:
        form = LoginForm()

    return render(request, "superadminloginapp/login.html", {"form": form, "error_message": error_message})
