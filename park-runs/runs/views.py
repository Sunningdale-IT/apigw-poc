"""
Views for Park Runs API
"""
from rest_framework import viewsets, filters
from .models import ParkRun
from .serializers import ParkRunSerializer, ParkRunListSerializer


class ParkRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Saturday park runs.
    Filter by active=true to get only current events.
    """
    queryset = ParkRun.objects.filter(active=True)
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'description']
    ordering_fields = ['start_time', 'distance_km', 'avg_participants']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ParkRunListSerializer
        return ParkRunSerializer
