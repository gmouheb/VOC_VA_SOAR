
from django.urls import path
from .views import  AnalystFileUploadView

urlpatterns = [

    path('upload/', AnalystFileUploadView.as_view(), name='analyst_file'),
]