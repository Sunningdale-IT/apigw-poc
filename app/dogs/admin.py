"""
Django admin configuration for dogs app.
"""
from django.contrib import admin
from .models import Dog


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'breed', 'latitude', 'longitude', 'caught_date']
    list_filter = ['breed', 'caught_date']
    search_fields = ['name', 'breed', 'comments']
    ordering = ['-caught_date']
