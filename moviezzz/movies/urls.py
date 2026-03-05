"""
URL configuration for movies API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CinemaViewSet, MovieViewSet

router = DefaultRouter()
router.register(r'cinemas', CinemaViewSet)
router.register(r'movies', MovieViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
