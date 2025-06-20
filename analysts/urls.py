
from django.urls import path
from .views import (
    RegisterAPIView, LoginAPIView, AnalystView, LogoutAPIView,
    generate_api_key, list_api_keys, delete_api_key
)

urlpatterns = [
    path('register', RegisterAPIView.as_view()),
    path('login', LoginAPIView.as_view()),
    path('logout', LogoutAPIView.as_view()),

    path('analyst', AnalystView.as_view()),
    # path('analysts/<int:pk>/delete/', AnalystDestroyAPIView.as_view(), name='analyst_delete'),

    # API key management
    path('api-keys/generate', generate_api_key, name='generate_api_key'),
    path('api-keys/list', list_api_keys, name='list_api_keys'),
    path('api-keys/delete/<int:key_id>', delete_api_key, name='delete_api_key'),
]
