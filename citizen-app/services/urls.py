"""
URL configuration for services app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('passport/', views.passport, name='passport'),
    path('driving-license/', views.driving_license, name='driving_license'),
    path('building-permit/', views.building_permit, name='building_permit'),
    path('trash-collection/', views.trash_collection, name='trash_collection'),
    path('found-dogs/', views.found_dogs, name='found_dogs'),
    path('found-dogs/<int:dog_id>/', views.found_dog_detail, name='found_dog_detail'),
]
