from django.urls import path
from . import views

app_name = 'cve_chat'

urlpatterns = [
    path('interface/', views.chat_interface, name='chat_interface'),
    path('interface/<int:vulnerability_id>/', views.chat_interface, name='chat_interface_with_vulnerability'),
    path('api/send-message/', views.send_message, name='send_message'),
]
