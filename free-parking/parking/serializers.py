"""
Serializers for Free Parking API
"""
from rest_framework import serializers
from .models import ParkingSpot


class ParkingSpotSerializer(serializers.ModelSerializer):
    """Serializer for parking spot details."""
    spot_type_display = serializers.CharField(source='get_spot_type_display', read_only=True)
    
    class Meta:
        model = ParkingSpot
        fields = [
            'id', 'spot_number', 'location', 'address', 'spot_type', 
            'spot_type_display', 'available', 'latitude', 'longitude',
            'hourly_rate', 'max_duration_hours', 'last_updated'
        ]
