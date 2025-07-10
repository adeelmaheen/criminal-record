from django.contrib import admin
from .models import CriminalRecord

class CriminalRecordAdmin(admin.ModelAdmin):
    list_display = ('defendant_name', 'case_number', 'parish', 'date_filed', 'alert_available')
    list_filter = ('parish', 'sex', 'race', 'alert_available')
    search_fields = ('defendant_name', 'case_number', 'charges')
    readonly_fields = ('scraped_timestamp',)
    date_hierarchy = 'date_filed'
    ordering = ('-date_filed',)

admin.site.register(CriminalRecord, CriminalRecordAdmin)

