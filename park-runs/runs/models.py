"""
Models for Park Runs - Saturday park running events
"""
from django.db import models


class ParkRun(models.Model):
    """Saturday park run event in the city."""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('moderate', 'Moderate'),
        ('challenging', 'Challenging'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    distance_km = models.DecimalField(max_digits=4, decimal_places=2, help_text='Distance in kilometers')
    start_time = models.TimeField(help_text='Saturday start time')
    meeting_point = models.CharField(max_length=255)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='moderate')
    
    organizer_name = models.CharField(max_length=255)
    organizer_email = models.EmailField()
    organizer_phone = models.CharField(max_length=20, blank=True)
    
    avg_participants = models.IntegerField(default=0, help_text='Average weekly participants')
    route_url = models.URLField(blank=True, help_text='Link to route map')
    
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_time', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.distance_km}km at {self.start_time.strftime('%H:%M')}"
