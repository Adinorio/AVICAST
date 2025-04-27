# dashboardadminapp/urls.py
from django.urls import path
from . import views

app_name = 'dashboardadminapp'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # User Management
    path('users/', views.users_view, name='users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),   # moved under users/
    path('users/restore/<int:user_id>/', views.restore_user, name='restore_user'),
    path('users/disable/<int:user_id>/', views.disable_user, name='disable_user'),
    path('users/archive/<int:user_id>/', views.archive_user, name='archive_user'),
    path('users/archived/', views.archived_users, name='archived_users'),

    # Other Pages
    path('roles/', views.roles_view, name='roles'),
    path('assign_roles/', views.assign_roles, name='assign_roles'),
    path('logs/', views.logs_view, name='logs'),
    
    # Logout
    path('logout/', views.custom_logout, name='logout'),
]
