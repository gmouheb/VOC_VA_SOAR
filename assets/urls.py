from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from assets import views

urlpatterns = [
    # API endpoints will be added here
]

urlpatterns = format_suffix_patterns(urlpatterns)