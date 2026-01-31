"""
Web URL configuration for dogs app (HTML views).
"""
from django.urls import path
from . import web_views

urlpatterns = [
    path('', web_views.index, name='index'),
    path('admin/', web_views.admin_page, name='admin'),
    path('add_dog', web_views.add_dog, name='add_dog'),
    path('browse', web_views.browse, name='browse'),
    path('delete_dog/<int:dog_id>', web_views.delete_dog, name='delete_dog'),
]
