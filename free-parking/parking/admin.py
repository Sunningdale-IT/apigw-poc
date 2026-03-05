from django.contrib import admin
from .models import ParkingSpot

@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ['spot_number', 'location', 'spot_type', 'available', 'last_updated']
    list_filter = ['available', 'spot_type']
    search_fields = ['spot_number', 'location', 'address']
