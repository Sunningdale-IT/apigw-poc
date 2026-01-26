from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import random

from .models import ProducedData, RequestLog
from .serializers import ProducedDataSerializer


class RequestLoggerMixin:
    """Mixin to log requests"""
    def log_request(self, request):
        RequestLog.objects.create(
            path=request.path,
            method=request.method
        )


class HomeView(View):
    """Home page view"""
    def get(self, request):
        return JsonResponse({
            'message': 'Producer Application',
            'admin_url': '/admin',
            'custom_admin_url': '/admin-dashboard',
            'endpoints': {
                'health': '/health',
                'api_data': '/api/data',
                'api_latest': '/api/data/latest',
                'api_produce': '/api/produce (POST)'
            }
        })


class AdminDashboardView(RequestLoggerMixin, View):
    """Custom admin dashboard view"""
    def get(self, request):
        self.log_request(request)
        
        # Get statistics
        total_data = ProducedData.objects.count()
        total_requests = RequestLog.objects.count()
        recent_data = ProducedData.objects.all()[:10]
        
        context = {
            'request_count': total_requests,
            'data_count': total_data,
            'data': recent_data,
        }
        
        return render(request, 'producer/admin_dashboard.html', context)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    return Response({
        'status': 'healthy',
        'service': 'producer',
        'timestamp': timezone.now().isoformat()
    })


@api_view(['POST'])
def produce_data(request):
    """Generate new data item"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    # Create new data item
    new_data = ProducedData.objects.create(
        value=random.randint(1, 100),
        producer='producer-service'
    )
    
    serializer = ProducedDataSerializer(new_data)
    
    return Response({
        'message': 'Data produced successfully',
        'data': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_all_data(request):
    """Retrieve all produced data"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    data = ProducedData.objects.all()
    serializer = ProducedDataSerializer(data, many=True)
    
    return Response({
        'count': data.count(),
        'data': serializer.data
    })


@api_view(['GET'])
def get_latest_data(request):
    """Get the latest data item"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    try:
        latest = ProducedData.objects.latest('timestamp')
        serializer = ProducedDataSerializer(latest)
        return Response(serializer.data)
    except ProducedData.DoesNotExist:
        return Response(
            {'message': 'No data available'},
            status=status.HTTP_404_NOT_FOUND
        )
