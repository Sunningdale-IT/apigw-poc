"""
URL configuration for records API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CitizenViewSet, RecordViewSet

router = DefaultRouter()
router.register(r'citizens', CitizenViewSet, basename='citizen')
router.register(r'records', RecordViewSet, basename='record')

urlpatterns = [
    path('', include(router.urls)),
]
