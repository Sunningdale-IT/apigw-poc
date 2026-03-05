from django.contrib import admin
from .models import Cinema, Movie


@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'screens']
    search_fields = ['name', 'address']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'director', 'genre', 'rating', 'runtime_minutes']
    list_filter = ['year', 'genre', 'rating']
    search_fields = ['title', 'director', 'plot']
    filter_horizontal = ['cinemas']
