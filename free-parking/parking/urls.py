"""
URL configuration for parking API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkingSpotViewSet

router = DefaultRouter()
router.register(r'spots', ParkingSpotViewSet, basename='parkingspot')

urlpatterns = [
    path('', include(router.urls)),
]
