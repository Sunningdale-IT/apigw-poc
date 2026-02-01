"""
API views for the Dogcatcher application.
"""
import os
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Dog
from .serializers import DogSerializer, DogInputSerializer, ExportSerializer


@csrf_exempt
def health(request):
    """Health check endpoint for Kubernetes probes."""
    return JsonResponse({'status': 'healthy', 'service': 'dogcatcher'})


@extend_schema_view(
    list=extend_schema(
        summary='List all dogs',
        description='Get a list of all caught dogs ordered by caught date.',
        responses={200: DogSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary='Get a dog by ID',
        description='Retrieve details of a specific dog.',
        responses={200: DogSerializer, 404: None}
    ),
    create=extend_schema(
        summary='Create a new dog entry',
        description='Add a new dog to the database.',
        request=DogInputSerializer,
        responses={201: DogSerializer, 400: None}
    ),
    destroy=extend_schema(
        summary='Delete a dog',
        description='Remove a dog from the database.',
        responses={204: None, 404: None}
    ),
)
class DogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dog model.
    Provides list, create, retrieve, and delete actions.
    """
    queryset = Dog.objects.all()
    serializer_class = DogSerializer
    http_method_names = ['get', 'post', 'delete']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DogInputSerializer
        return DogSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Delete photo file if it exists
        if instance.photo_filename:
            photo_path = os.path.join(settings.MEDIA_ROOT, instance.photo_filename)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except OSError:
                    pass
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @extend_schema(
        summary='Download dog photo',
        description='Download the photo of a specific dog.',
        responses={
            (200, 'image/*'): OpenApiTypes.BINARY,
            404: None
        }
    )
    @action(detail=True, methods=['get'], url_path='photo')
    def photo(self, request, pk=None):
        """Download a dog's photo."""
        dog = self.get_object()
        
        if not dog.photo_filename:
            raise Http404('No photo available for this dog')
        
        photo_path = os.path.join(settings.MEDIA_ROOT, dog.photo_filename)
        if not os.path.exists(photo_path):
            raise Http404('Photo file not found')
        
        return FileResponse(
            open(photo_path, 'rb'),
            content_type='image/jpeg'
        )
    
    @extend_schema(
        summary='Export all dogs',
        description='Export all dogs data with metadata.',
        responses={200: ExportSerializer}
    )
    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        """Export all dogs data."""
        dogs = Dog.objects.all()
        serializer = DogSerializer(dogs, many=True)
        
        export_data = {
            'total_count': dogs.count(),
            'exported_at': timezone.now(),
            'dogs': serializer.data
        }
        
        return Response(ExportSerializer(export_data).data)
