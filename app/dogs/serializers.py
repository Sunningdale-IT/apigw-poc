"""
Serializers for the Dogcatcher API.
"""
from rest_framework import serializers
from .models import Dog


class DogSerializer(serializers.ModelSerializer):
    """Serializer for Dog model."""
    
    photo_url = serializers.SerializerMethodField()
    photo_download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Dog
        fields = [
            'id', 'name', 'latitude', 'longitude', 'breed',
            'photo_filename', 'photo_url', 'photo_download_url',
            'comments', 'caught_date'
        ]
        read_only_fields = ['id', 'caught_date', 'photo_url', 'photo_download_url']
    
    def get_photo_url(self, obj):
        if obj.photo_filename:
            return f'/static/uploads/{obj.photo_filename}'
        return None
    
    def get_photo_download_url(self, obj):
        """Return photo download URL (relative path for use with Kong gateway)."""
        if obj.photo_filename:
            return f'/dogs/{obj.id}/photo/'
        return None


class DogInputSerializer(serializers.ModelSerializer):
    """Serializer for creating Dog entries."""
    
    class Meta:
        model = Dog
        fields = ['name', 'latitude', 'longitude', 'breed', 'comments']
    
    def validate_latitude(self, value):
        if value < -90 or value > 90:
            raise serializers.ValidationError('Latitude must be between -90 and 90')
        return value
    
    def validate_longitude(self, value):
        if value < -180 or value > 180:
            raise serializers.ValidationError('Longitude must be between -180 and 180')
        return value


class ExportSerializer(serializers.Serializer):
    """Serializer for export endpoint."""
    
    total_count = serializers.IntegerField()
    exported_at = serializers.DateTimeField()
    dogs = DogSerializer(many=True)
