from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('health', views.health_check, name='health'),
    path('api/consume', views.consume_data, name='consume'),
    path('api/trigger-produce', views.trigger_produce, name='trigger-produce'),
    path('api/consumed', views.get_consumed_data, name='consumed-data'),
]
