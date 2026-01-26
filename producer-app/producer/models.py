from django.db import models
from django.utils import timezone


class ProducedData(models.Model):
    """Model to store produced data items"""
    value = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    producer = models.CharField(max_length=100, default='producer-service')
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Produced Data'
        verbose_name_plural = 'Produced Data Items'
    
    def __str__(self):
        return f"Data #{self.id} - Value: {self.value}"


class RequestLog(models.Model):
    """Model to log API requests for statistics"""
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.method} {self.path} at {self.timestamp}"
