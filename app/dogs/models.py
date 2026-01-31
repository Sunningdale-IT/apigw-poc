"""
Dog model for the Dogcatcher application.
"""
from django.db import models
from django.utils import timezone


class Dog(models.Model):
    """Model representing a caught dog."""
    
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    breed = models.CharField(max_length=100)
    photo_filename = models.CharField(max_length=255, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    caught_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'dogs'
        ordering = ['-caught_date']
    
    def __str__(self):
        return f"{self.name} ({self.breed})"
    
    @property
    def photo_url(self):
        """Return the URL to the photo if it exists."""
        if self.photo_filename:
            return f'/static/uploads/{self.photo_filename}'
        return None
    
    @property
    def photo_download_url(self):
        """Return the API endpoint to download the photo (with trailing slash for Django)."""
        if self.photo_filename:
            return f'/dogs/{self.id}/photo/'
        return None
