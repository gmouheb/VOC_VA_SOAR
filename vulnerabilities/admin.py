from django.contrib import admin
from django.contrib import admin
from .models import Vulnerability

@admin.register(Vulnerability)
class VulnerabilityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'severity', 'cvss_score', 'discovered_date', 'analyst')
    list_filter = ('severity', 'discovered_date', 'analyst')
    search_fields = ('name', 'description', 'affected_asset')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Risk Assessment', {
            'fields': ('severity', 'cvss_score', 'epss')
        }),
        ('Asset & Remediation', {
            'fields': ('affected_asset', 'remediation')
        }),
        ('Audit', {
            'fields': ('discovered_date', 'analyst', 'created_at', 'updated_at')
        }),
    )
# Register your models here.
