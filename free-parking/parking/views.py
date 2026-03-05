"""
Views for Free Parking API
"""
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ParkingSpot
from .serializers import ParkingSpotSerializer


class ParkingSpotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for parking spots.
    Filter by available=true to get only free spots.
    """
    queryset = ParkingSpot.objects.all()
    serializer_class = ParkingSpotSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['available', 'spot_type', 'location']
    search_fields = ['spot_number', 'location', 'address']
    ordering_fields = ['last_updated', 'hourly_rate', 'spot_number']
