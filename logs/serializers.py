from rest_framework import serializers
from .models import Log

class LogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Log
        fields = ['id', 'user', 'event', 'timestamp', 'metadata'] 