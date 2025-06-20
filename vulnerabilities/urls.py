from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VulnerabilityViewSet, ImportVulnerabilitiesView, get_vulnerabilities_json, get_vulnerabilities_api

router = DefaultRouter()
router.register(r'vulnerabilities', VulnerabilityViewSet, basename='vulnerability')

urlpatterns = [
    path('', include(router.urls)),
    path('import', ImportVulnerabilitiesView.as_view(), name='import-vulnerabilities'),
    path('listvul', get_vulnerabilities_json, name='vulnerabilities-json'),
    path('api/vulnerabilities', get_vulnerabilities_api, name='vulnerabilities-api'),
]
