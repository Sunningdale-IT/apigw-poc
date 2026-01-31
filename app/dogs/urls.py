"""
API URL configuration for dogs app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DogViewSet

router = DefaultRouter()
router.register(r'dogs', DogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
