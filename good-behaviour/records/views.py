"""
Views for Good Behaviour API
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Citizen, CriminalRecord
from .serializers import CitizenSerializer, CitizenListSerializer, RecordSerializer


class CitizenViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for citizens and their good behaviour records.
    Use /api/citizens/{citizen_id}/check/ to get record by citizen ID.
    """
    queryset = Citizen.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['citizen_id', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action == 'list':
            return CitizenListSerializer
        return CitizenSerializer

    @action(detail=False, methods=['get'], url_path='check/(?P<citizen_id>[^/.]+)')
    def check(self, request, citizen_id=None):
        """Check good behaviour record by citizen ID."""
        try:
            citizen = Citizen.objects.get(citizen_id=citizen_id)
            serializer = CitizenSerializer(citizen)
            return Response(serializer.data)
        except Citizen.DoesNotExist:
            return Response({
                'citizen_id': citizen_id,
                'found': False,
                'message': 'Citizen not found in database'
            }, status=404)


class RecordViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for good behaviour records."""
    queryset = CriminalRecord.objects.all()
    serializer_class = RecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['severity', 'status', 'offense_type', 'citizen']
    ordering_fields = ['offense_date', 'created_at']
