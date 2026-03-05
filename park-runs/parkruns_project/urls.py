"""
URL configuration for parkruns_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def health_check(request):
    return HttpResponse('OK')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('runs.urls')),
    path('health/', health_check),
]
