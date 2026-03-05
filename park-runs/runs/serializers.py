"""
Serializers for Park Runs API
"""
from rest_framework import serializers
from .models import ParkRun


class ParkRunSerializer(serializers.ModelSerializer):
    """Serializer for park run details."""
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    class Meta:
        model = ParkRun
        fields = [
            'id', 'name', 'location', 'description', 'distance_km', 'start_time',
            'meeting_point', 'difficulty', 'difficulty_display', 'organizer_name',
            'organizer_email', 'organizer_phone', 'avg_participants', 'route_url',
            'latitude', 'longitude', 'active', 'created_at'
        ]


class ParkRunListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for park run list."""
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    
    class Meta:
        model = ParkRun
        fields = [
            'id', 'name', 'location', 'distance_km', 'start_time',
            'difficulty', 'difficulty_display', 'avg_participants', 'active'
        ]
