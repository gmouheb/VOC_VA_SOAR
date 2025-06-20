"""
URL configuration for PFE_VOC project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render

from analysts.template_views import (
    login_view, register_view, logout_view, profile_view, 
    edit_profile_view, change_password_view, dashboard_view,
    api_key_management_view, landing_page_view
)
from vulnerabilities.template_views import (
    vulnerability_list_view, vulnerability_detail_view, import_vulnerabilities_view
)
from analyst_file.template_views import file_upload_view
from assets.template_views import asset_list_view, asset_detail_view, create_asset_view, edit_asset_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/analyst/', include('analysts.urls')),
    path('api/file/', include('analyst_file.urls')),
    path('api/security/', include('vulnerabilities.urls')),
    path('api/asset/', include('assets.urls')),
    path('api/cve-chat/', include('cve_chat.urls')),

    # Template views
    path('', landing_page_view, name='landing_page'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),
    path('profile/change-password/', change_password_view, name='change_password'),
    path('api-keys/', api_key_management_view, name='api_key_management'),
    path('vulnerabilities/', vulnerability_list_view, name='vulnerability_list'),
    path('vulnerabilities/<int:pk>/', vulnerability_detail_view, name='vulnerability_detail'),
    path('vulnerabilities/import/', import_vulnerabilities_view, name='import_vulnerabilities'),
    path('files/upload/', file_upload_view, name='file_upload'),
    path('assets/', asset_list_view, name='asset_list'),
    path('assets/<int:pk>/', asset_detail_view, name='asset_detail'),
    path('assets/create/', create_asset_view, name='create_asset'),
    path('assets/<int:pk>/edit/', edit_asset_view, name='edit_asset'),

    # CVE Remediation
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Define custom 404 handler
def page_not_found(request, exception):
    return render(request, '404.html', status=404)

# Register the custom 404 handler
handler404 = 'PFE_VOC.urls.page_not_found'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
