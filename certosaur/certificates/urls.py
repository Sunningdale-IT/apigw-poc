"""
URL configuration for Certosaur certificates app. 🦖
"""

from django.urls import path
from . import views

urlpatterns = [
    # Health check
    path('health/', views.health, name='health'),
    
    # Home / Dashboard
    path('', views.index, name='index'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Certificate Authorities
    path('ca/', views.ca_list, name='ca_list'),
    path('ca/create/', views.ca_create, name='ca_create'),
    path('ca/<uuid:pk>/', views.ca_detail, name='ca_detail'),
    path('ca/<uuid:pk>/download/<str:file_type>/', views.ca_download, name='ca_download'),
    path('ca/<uuid:pk>/delete/', views.ca_delete, name='ca_delete'),
    
    # Server Certificates
    path('server/', views.server_cert_list, name='server_cert_list'),
    path('server/create/', views.server_cert_create, name='server_cert_create'),
    path('server/<uuid:pk>/', views.server_cert_detail, name='server_cert_detail'),
    path('server/<uuid:pk>/download/<str:file_type>/', views.server_cert_download, name='server_cert_download'),
    path('server/<uuid:pk>/revoke/', views.server_cert_revoke, name='server_cert_revoke'),
    path('server/<uuid:pk>/delete/', views.server_cert_delete, name='server_cert_delete'),
    
    # Client Certificates
    path('client/', views.client_cert_list, name='client_cert_list'),
    path('client/create/', views.client_cert_create, name='client_cert_create'),
    path('client/<uuid:pk>/', views.client_cert_detail, name='client_cert_detail'),
    path('client/<uuid:pk>/download/<str:file_type>/', views.client_cert_download, name='client_cert_download'),
    path('client/<uuid:pk>/revoke/', views.client_cert_revoke, name='client_cert_revoke'),
    path('client/<uuid:pk>/delete/', views.client_cert_delete, name='client_cert_delete'),
]
