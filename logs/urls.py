from rest_framework import routers
from .views import LogViewSet

router = routers.DefaultRouter()
router.register(r'logs', LogViewSet)

urlpatterns = router.urls 