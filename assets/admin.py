from django.contrib import admin
from .models import Asset

# Register your models here.
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_name', 'asset_type', 'company', 'asset_criticality', 'state', 'asset_true_risk_score', 'asset_exposure', 'owner')
    list_filter = ('asset_type', 'company', 'asset_criticality', 'state', 'asset_exposure', 'owner')
    search_fields = ('asset_name', 'company', 'owner__email')
    filter_horizontal = ('vulnerabilities',)
    readonly_fields = ('asset_true_risk_score',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('asset_name', 'asset_type', 'company', 'owner')
        }),
        ('Risk Assessment', {
            'fields': ('asset_criticality', 'asset_exposure', 'asset_true_risk_score')
        }),
        ('Status', {
            'fields': ('state',)
        }),
        ('Vulnerabilities', {
            'fields': ('vulnerabilities',)
        }),
    )

admin.site.register(Asset, AssetAdmin)
