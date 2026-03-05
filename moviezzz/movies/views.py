"""
Views for Movies API
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cinema, Movie
from .serializers import CinemaSerializer, MovieSerializer, MovieListSerializer


class CinemaViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing cinemas."""
    queryset = Cinema.objects.all()
    serializer_class = CinemaSerializer
    
    @action(detail=True, methods=['get'])
    def movies(self, request, pk=None):
        """Get all movies showing at this cinema."""
        cinema = self.get_object()
        movies = cinema.movies.all()
        serializer = MovieListSerializer(movies, many=True)
        return Response(serializer.data)


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing movies."""
    queryset = Movie.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MovieListSerializer
        return MovieSerializer
    
    @action(detail=False, methods=['get'])
    def by_cinema(self, request):
        """Group movies by cinema."""
        cinemas = Cinema.objects.all()
        result = []
        for cinema in cinemas:
            movies = cinema.movies.all()
            result.append({
                'cinema': CinemaSerializer(cinema).data,
                'movies': MovieListSerializer(movies, many=True).data
            })
        return Response(result)
