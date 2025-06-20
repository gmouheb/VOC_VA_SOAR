from django.contrib import admin
from .models import AnalystFile

# Register your models here.
class AnalystFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_type', 'scanner_source', 'analyst', 'created_at', 'is_xml_file')
    list_filter = ('file_type', 'scanner_source', 'created_at', 'analyst')
    search_fields = ('filename', 'file_type', 'scanner_source', 'analyst__email')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('File Information', {
            'fields': ('filename', 'file_type', 'upload', 'scanner_source')
        }),
        ('Ownership', {
            'fields': ('analyst',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def is_xml_file(self, obj):
        """Display whether the file is an XML file"""
        return obj.is_xml
    is_xml_file.short_description = "Is XML"
    is_xml_file.boolean = True

admin.site.register(AnalystFile, AnalystFileAdmin)
