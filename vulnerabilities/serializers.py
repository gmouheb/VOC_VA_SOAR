from rest_framework import serializers
from .models import Vulnerability

class VulnerabilitySerializer(serializers.ModelSerializer):
    analyst_email = serializers.ReadOnlyField(source='analyst.email')

    class Meta:
        model = Vulnerability
        fields = [
            'id', 
            'name', 
            'port',
            'protocol',
            'description', 
            'severity', 
            'cvss_score', 
            'cve',
            'affected_asset', 
            'remediation', 
            'risk_factor',
            'see_also',
            'xref',
            'epss', 
            'discovered_date', 
            'analyst', 
            'analyst_email',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_cvss_score(self, value):
        """Validate CVSS score is between 0 and 10"""
        if value < 0 or value > 10:
            raise serializers.ValidationError("CVSS score must be between 0 and 10")
        return value

    def create(self, validated_data):
        """Create a new vulnerability with the current user as analyst"""
        # Get the analyst from the context if not provided in data
        if 'analyst' not in validated_data and 'request' in self.context:
            validated_data['analyst'] = self.context['request'].user
        return super().create(validated_data)

class VulnerabilityAPISerializer(serializers.ModelSerializer):
    """
    Serializer for the Vulnerability API that includes all fields except analyst
    and includes the true_risk_score field.
    """
    class Meta:
        model = Vulnerability
        fields = [
            'id', 
            'name', 
            'port',
            'protocol',
            'description', 
            'severity', 
            'cvss_score', 
            'cve',
            'affected_asset', 
            'remediation', 
            'risk_factor',
            'see_also',
            'xref',
            'epss', 
            'true_risk_score',
            'discovered_date', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
