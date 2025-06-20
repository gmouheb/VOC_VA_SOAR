from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import Analyst, APIKey
import analysts


# Register your models here.


class AnalystChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Analyst


class AnalystCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Analyst
        fields = ('email',)


class UserAdmin(BaseUserAdmin):
    form = AnalystChangeForm
    add_form = AnalystCreationForm
    model = Analyst
    list_display = ('email', 'first_name', 'last_name', 'company', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'company')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'company', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


admin.site.register(Analyst, UserAdmin)

class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('name', 'key_preview', 'analyst', 'created_at', 'last_used')
    list_filter = ('created_at', 'last_used', 'analyst')
    search_fields = ('name', 'key', 'analyst__email')
    readonly_fields = ('key', 'created_at', 'last_used')

    def key_preview(self, obj):
        """Display a preview of the API key"""
        return f"{obj.key[:8]}..." if obj.key else ""
    key_preview.short_description = "API Key"

admin.site.register(APIKey, APIKeyAdmin)
