"""
URL configuration for runs API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ParkRunViewSet

router = DefaultRouter()
router.register(r'parkruns', ParkRunViewSet, basename='parkrun')

urlpatterns = [
    path('', include(router.urls)),
]
