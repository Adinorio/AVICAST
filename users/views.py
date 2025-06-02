from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer
from logs.models import Log
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from logs.serializers import LogSerializer
from rest_framework.authtoken.models import Token

# Create your views here.

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SUPER_ADMIN'

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]

    def perform_create(self, serializer):
        user = serializer.save()
        Log.objects.create(user=self.request.user, event=f"Created user {user.username}")

    def perform_update(self, serializer):
        user = serializer.save()
        Log.objects.create(user=self.request.user, event=f"Updated user {user.username}")

    def perform_destroy(self, instance):
        Log.objects.create(user=self.request.user, event=f"Deleted user {instance.username}")
        instance.delete()

class DashboardSummaryView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        # User counts by role
        user_counts = {
            role: User.objects.filter(role=role).count()
            for role, _ in User.ROLE_CHOICES
        }
        # Recent log entries
        recent_logs = Log.objects.all().order_by('-timestamp')[:10]
        recent_logs_data = LogSerializer(recent_logs, many=True).data
        return Response({
            'user_counts': user_counts,
            'recent_logs': recent_logs_data,
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
            return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            return Response({'detail': 'Token not found.'}, status=status.HTTP_400_BAD_REQUEST)
