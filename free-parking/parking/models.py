"""
Models for Free Parking - Available parking spots
"""
from django.db import models


class ParkingSpot(models.Model):
    """Available parking spot in the city."""
    SPOT_TYPES = [
        ('street', 'Street Parking'),
        ('garage', 'Parking Garage'),
        ('lot', 'Parking Lot'),
        ('disabled', 'Disabled Parking'),
        ('ev', 'EV Charging'),
    ]
    
    spot_number = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    spot_type = models.CharField(max_length=20, choices=SPOT_TYPES, default='street')
    available = models.BooleanField(default=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Rate per hour in currency')
    max_duration_hours = models.IntegerField(default=24, help_text='Maximum parking duration in hours')
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['location', 'spot_number']
    
    def __str__(self):
        status = "Available" if self.available else "Occupied"
        return f"{self.spot_number} - {self.location} ({status})"
