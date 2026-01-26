from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('health', views.health_check, name='health'),
    path('api/produce', views.produce_data, name='produce'),
    path('api/data', views.get_all_data, name='all-data'),
    path('api/data/latest', views.get_latest_data, name='latest-data'),
]
