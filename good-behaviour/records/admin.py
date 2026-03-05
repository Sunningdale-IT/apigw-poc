from django.contrib import admin
from .models import Citizen, CriminalRecord

@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ['citizen_id', 'first_name', 'last_name', 'date_of_birth', 'record_count']
    search_fields = ['citizen_id', 'first_name', 'last_name']
    
    def record_count(self, obj):
        return obj.criminal_records.count()
    record_count.short_description = 'Criminal Records'

@admin.register(CriminalRecord)
class CriminalRecordAdmin(admin.ModelAdmin):
    list_display = ['citizen', 'offense_type', 'offense_date', 'severity', 'status']
    list_filter = ['severity', 'status', 'offense_type']
    search_fields = ['citizen__citizen_id', 'citizen__first_name', 'citizen__last_name', 'description']
