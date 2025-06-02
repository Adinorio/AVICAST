from rest_framework import routers
from django.urls import path
from .views import UserViewSet, DashboardSummaryView, LogoutView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = router.urls
urlpatterns += [
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
] 