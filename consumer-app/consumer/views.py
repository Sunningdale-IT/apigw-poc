from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import logging

from .models import ConsumedData, RequestLog, APICallLog
from .serializers import ConsumedDataSerializer

logger = logging.getLogger(__name__)


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
            'message': 'Consumer Application',
            'admin_url': '/admin',
            'custom_admin_url': '/admin-dashboard',
            'endpoints': {
                'health': '/health',
                'api_consume': '/api/consume',
                'api_trigger_produce': '/api/trigger-produce (POST)',
                'api_consumed': '/api/consumed'
            }
        })


class AdminDashboardView(RequestLoggerMixin, View):
    """Custom admin dashboard view"""
    def get(self, request):
        self.log_request(request)
        
        # Get statistics
        total_consumed = ConsumedData.objects.count()
        total_requests = RequestLog.objects.count()
        total_api_calls = APICallLog.objects.count()
        recent_data = ConsumedData.objects.all()[:10]
        
        context = {
            'request_count': total_requests,
            'data_count': total_consumed,
            'api_calls': total_api_calls,
            'data': recent_data,
            'producer_url': settings.PRODUCER_API_URL,
        }
        
        return render(request, 'consumer/admin_dashboard.html', context)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    return Response({
        'status': 'healthy',
        'service': 'consumer',
        'timestamp': timezone.now().isoformat(),
        'producer_api_url': settings.PRODUCER_API_URL
    })


@api_view(['GET'])
def consume_data(request):
    """Fetch data from Producer via Kong API Gateway"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    try:
        # Call Producer API through Kong Gateway
        api_url = f'{settings.PRODUCER_API_URL}/api/data/latest'
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Log successful API call
            APICallLog.objects.create(
                endpoint=api_url,
                success=True
            )
            
            # Store consumed data
            consumed_item = ConsumedData.objects.create(
                producer_id=data.get('id'),
                value=data.get('value'),
                producer_timestamp=parse_datetime(data.get('timestamp')),
                producer_name=data.get('producer', 'producer-service')
            )
            
            serializer = ConsumedDataSerializer(consumed_item)
            
            return Response({
                'message': 'Data consumed successfully via Kong API Gateway',
                'data': serializer.data,
                'via_gateway': True
            })
        else:
            # Log failed API call
            APICallLog.objects.create(
                endpoint=api_url,
                success=False
            )
            
            return Response({
                'error': 'Failed to fetch data from Producer',
                'status_code': response.status_code
            }, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Producer via Kong: {str(e)}")
        
        # Log failed API call
        APICallLog.objects.create(
            endpoint=settings.PRODUCER_API_URL,
            success=False
        )
        
        return Response({
            'error': 'Failed to connect to Producer via Kong API Gateway',
            'details': str(e),
            'producer_url': settings.PRODUCER_API_URL
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def trigger_produce(request):
    """Trigger Producer to generate new data via Kong"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    try:
        # Call Producer API through Kong Gateway
        api_url = f'{settings.PRODUCER_API_URL}/api/produce'
        response = requests.post(api_url, timeout=5)
        
        if response.status_code == 201:
            data = response.json()
            
            # Log successful API call
            APICallLog.objects.create(
                endpoint=api_url,
                success=True
            )
            
            return Response({
                'message': 'Successfully triggered Producer via Kong API Gateway',
                'data': data,
                'via_gateway': True
            })
        else:
            # Log failed API call
            APICallLog.objects.create(
                endpoint=api_url,
                success=False
            )
            
            return Response({
                'error': 'Failed to trigger Producer',
                'status_code': response.status_code
            }, status=response.status_code)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Producer via Kong: {str(e)}")
        
        # Log failed API call
        APICallLog.objects.create(
            endpoint=settings.PRODUCER_API_URL,
            success=False
        )
        
        return Response({
            'error': 'Failed to connect to Producer via Kong API Gateway',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_consumed_data(request):
    """Retrieve all consumed data"""
    RequestLog.objects.create(path=request.path, method=request.method)
    
    data = ConsumedData.objects.all()
    serializer = ConsumedDataSerializer(data, many=True)
    
    return Response({
        'count': data.count(),
        'data': serializer.data
    })
