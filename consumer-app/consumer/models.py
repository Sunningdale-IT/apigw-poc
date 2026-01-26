from django.db import models
from django.utils import timezone


class ConsumedData(models.Model):
    """Model to store consumed data items"""
    producer_id = models.IntegerField()
    value = models.IntegerField()
    producer_timestamp = models.DateTimeField()
    consumed_at = models.DateTimeField(default=timezone.now)
    producer_name = models.CharField(max_length=100, default='producer-service')
    
    class Meta:
        ordering = ['-consumed_at']
        verbose_name = 'Consumed Data'
        verbose_name_plural = 'Consumed Data Items'
    
    def __str__(self):
        return f"Consumed #{self.producer_id} - Value: {self.value}"


class RequestLog(models.Model):
    """Model to log API requests for statistics"""
    path = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.method} {self.path} at {self.timestamp}"


class APICallLog(models.Model):
    """Model to log API calls to Producer via Kong"""
    endpoint = models.CharField(max_length=255)
    success = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.endpoint} at {self.timestamp}"
