from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def user_management(request):
    return render(request, 'user-management.html')

@login_required
def assignment(request):
    return render(request, 'assignment.html')

@login_required
def history(request):
    return render(request, 'history.html')

@login_required
def notifications(request):
    return render(request, 'notifications.html')

@login_required
def settings(request):
    return render(request, 'settings.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login') 