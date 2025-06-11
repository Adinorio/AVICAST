# dashboardadminapp/urls.py
from django.urls import path
from . import views

app_name = 'user_management' # Updated app_name

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    # User Management
    path('users/', views.users_view, name='users'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<str:user_id>/', views.edit_user, name='edit_user'),
    path('users/update/', views.edit_user, name='update_user'),
    path('users/disable/<int:user_id>/', views.disable_user, name='disable_user'),
    path('users/archived/', views.archived_users, name='archived_users'),
    path('users/restore/<int:user_id>/', views.restore_user, name='restore_user'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/stats/', views.get_user_stats, name='user_stats'),

    # Other Pages
    path('roles/', views.roles_view, name='roles'),
    path('roles/assign/', views.assign_roles, name='assign_roles'),
    path('logs/', views.logs_view, name='logs'),
    
    # Logout
    path('logout/', views.custom_logout, name='logout'),
    path('forgot-password/', views.forgot_password_request, name='forgot_password'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('settings/', views.settings_view, name='settings'),
    path('update_permission/', views.update_permission, name='update_permission'),
] 