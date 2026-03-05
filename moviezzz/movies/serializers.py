"""
Serializers for Movies API
"""
from rest_framework import serializers
from .models import Cinema, Movie


class CinemaSerializer(serializers.ModelSerializer):
    """Serializer for Cinema model."""
    
    class Meta:
        model = Cinema
        fields = ['id', 'name', 'address', 'phone', 'screens']


class MovieSerializer(serializers.ModelSerializer):
    """Serializer for Movie model."""
    cinemas = CinemaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'plot', 'director', 'runtime_minutes',
            'rating', 'year', 'genre', 'cinemas', 'showtimes'
        ]


class MovieListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for movie lists."""
    cinema_names = serializers.SerializerMethodField()
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'director', 'runtime_minutes',
            'rating', 'year', 'genre', 'cinema_names'
        ]
    
    def get_cinema_names(self, obj):
        return [cinema.name for cinema in obj.cinemas.all()]
