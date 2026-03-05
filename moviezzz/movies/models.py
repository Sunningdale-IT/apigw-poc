"""
Models for Moviezzz - Cinema and Movie data
"""
from django.db import models


class Cinema(models.Model):
    """Cinema location in town."""
    name = models.CharField(max_length=255, unique=True)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    screens = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Movie(models.Model):
    """Movie showing in cinemas."""
    title = models.CharField(max_length=255)
    plot = models.TextField()
    director = models.CharField(max_length=255, default='Unknown')
    runtime_minutes = models.IntegerField(default=90)
    rating = models.CharField(max_length=10, default='R')
    year = models.IntegerField(default=2024)
    genre = models.CharField(max_length=100, default='Action')
    
    # Showing details
    cinemas = models.ManyToManyField(Cinema, related_name='movies')
    showtimes = models.JSONField(default=list, help_text='List of showtime strings')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['title']
    
    def __str__(self):
        return f"{self.title} ({self.year})"
