from django.contrib import admin
from .models import ConsumedData, RequestLog, APICallLog


class ConsumedDataAdmin(admin.ModelAdmin):
    list_display = ['producer_id', 'value', 'producer_name', 'producer_timestamp', 'consumed_at']
    list_filter = ['consumed_at', 'producer_name']
    search_fields = ['producer_id', 'value']
    readonly_fields = ['consumed_at']


class RequestLogAdmin(admin.ModelAdmin):
    list_display = ['method', 'path', 'timestamp']
    list_filter = ['method', 'timestamp']
    search_fields = ['path']
    readonly_fields = ['timestamp']


class APICallLogAdmin(admin.ModelAdmin):
    list_display = ['endpoint', 'success', 'timestamp']
    list_filter = ['success', 'timestamp']
    search_fields = ['endpoint']
    readonly_fields = ['timestamp']


admin.site.register(ConsumedData, ConsumedDataAdmin)
admin.site.register(RequestLog, RequestLogAdmin)
admin.site.register(APICallLog, APICallLogAdmin)

# Customize admin site
admin.site.site_header = "Consumer Application Admin"
admin.site.site_title = "Consumer Admin"
admin.site.index_title = "Welcome to Consumer Administration"
