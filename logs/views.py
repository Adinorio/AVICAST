from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Log
from .serializers import LogSerializer
from users.views import IsSuperAdmin

# Create your views here.

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all().order_by('-timestamp')
    serializer_class = LogSerializer
    permission_classes = [IsSuperAdmin]
