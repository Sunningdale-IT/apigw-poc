from django.contrib import admin
from .models import ProducedData, RequestLog


class ProducedDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'value', 'producer', 'timestamp']
    list_filter = ['timestamp', 'producer']
    search_fields = ['id', 'value']
    readonly_fields = ['timestamp']


class RequestLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'timestamp']
    list_filter = ['method', 'timestamp']
    search_fields = ['path']
    readonly_fields = ['timestamp']


admin.site.register(ProducedData, ProducedDataAdmin)
admin.site.register(RequestLog, RequestLogAdmin)

# Customize admin site
admin.site.site_header = "Producer Application Admin"
admin.site.site_title = "Producer Admin"
admin.site.index_title = "Welcome to Producer Administration"
