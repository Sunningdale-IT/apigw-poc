from django.contrib import admin
from .models import ParkRun

@admin.register(ParkRun)
class ParkRunAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'distance_km', 'start_time', 'avg_participants', 'active']
    list_filter = ['active', 'difficulty']
    search_fields = ['name', 'location', 'description']
