from rest_framework import serializers
from .models import AnalystFile

class AnalystFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalystFile
        fields = ['id', 'filename', 'file_type', 'upload', 'analyst', 'created_at', 'scanner_source']
        read_only_fields = ['id', 'created_at']
