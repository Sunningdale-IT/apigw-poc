"""
API URL configuration for dogs app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dogs', views.DogViewSet)

urlpatterns = [
    path('health/', views.health, name='health'),
    path('', include(router.urls)),
]
