from django.db import models
from django.db import models
from analysts.models import Analyst
from django.db.models.signals import post_save
from django.dispatch import receiver

class Vulnerability(models.Model):
    SEVERITY_CHOICES = [
        (4, 'Critical'),
        (3, 'High'),
        (2, 'Medium'),
        (1, 'Low'),
        (0, 'Info'),
    ]

    name = models.CharField(max_length=255)  # Hostname or IP address
    port = models.CharField(max_length=10, blank=True, null=True)  # Port number where the issue was found
    protocol = models.CharField(max_length=20, blank=True, null=True)  # Protocol
    description = models.TextField()  # Full description of the issue
    severity = models.IntegerField(choices=SEVERITY_CHOICES)  # Numeric value: 0 (Info) to 4 (Critical)
    cvss_score = models.FloatField()
    cve = models.TextField(blank=True, null=True)  # CVE ID(s) (comma-separated if multiple)
    affected_asset = models.CharField(max_length=255)
    remediation = models.TextField()  # Recommended remediation or fix
    risk_factor = models.CharField(max_length=20, blank=True, null=True)  # Qualitative risk: Low, Medium, High, Critical
    see_also = models.TextField(blank=True, null=True)  # Related references (URLs, advisories, etc.)
    xref = models.TextField(blank=True, null=True)  # Cross references
    epss = models.CharField(max_length=50, blank=True, null=True)  # Exploitation Probability Scoring System
    true_risk_score = models.FloatField(null=True, blank=True)  # Individual true risk score for this vulnerability
    discovered_date = models.DateField()
    analyst = models.ForeignKey(Analyst, on_delete=models.CASCADE, related_name='vulnerabilities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (ID: {self.id})"

    def has_exposed_asset(self):
        """
        Check if any of the associated assets are exposed to the internet.
        Returns True if at least one asset is exposed, False otherwise.
        """
        return self.assets.filter(asset_exposure=True).exists()

    class Meta:
        ordering = ['-severity', 'discovered_date']  # Order by severity then by date
        verbose_name = 'Vulnerability'
        verbose_name_plural = 'Vulnerabilities'

@receiver(post_save, sender=Vulnerability)
def create_or_update_asset(sender, instance, created, **kwargs):
    """
    Signal handler to automatically create or update an Asset when a Vulnerability is saved.
    Uses the hostname/IP from the Vulnerability as the asset name.
    """
    from assets.models import Asset

    # Get or create the Asset based on the name (hostname/IP)
    asset, created = Asset.objects.get_or_create(
        asset_name=instance.name,
        owner=instance.analyst,
        defaults={
            'asset_type': 'Server',  # Default type
            'company': instance.analyst.company,
            'asset_criticality': 1,  # Default to Low criticality
            'state': 'open',  # Use the default value
            'asset_true_risk_score': None
        }
    )

    # Add this vulnerability to the asset's vulnerabilities
    asset.vulnerabilities.add(instance)

    # Recalculate the asset's true risk score
    new_score = asset.calculate_true_risk_score()
    if new_score is not None:
        Asset.objects.filter(pk=asset.pk).update(asset_true_risk_score=new_score)

    # Ensure the vulnerability's true_risk_score is also updated
    # This is needed because sometimes the vulnerability might not be properly associated with the asset
    # when the asset's calculate_true_risk_score method is called
    if instance.true_risk_score is None:
        # Get the CVSS score (AS)
        cvss = instance.cvss_score

        # Get the EPSS value (EL)
        try:
            epss = float(instance.epss) if instance.epss else 1.0
        except ValueError:
            epss = 1.0

        # Get the asset criticality (AC)
        ac = asset.asset_criticality

        # Get the asset exposure (AE)
        ae = 1.0 if asset.asset_exposure else 0.5

        # Get the severity value
        severity = instance.severity

        # Get the risk factor value
        risk_factor_value = 1.0  # Default value
        if instance.risk_factor:
            risk_factor = instance.risk_factor.lower()
            if risk_factor == 'low':
                risk_factor_value = 0.15
            elif risk_factor == 'medium':
                risk_factor_value = 0.25
            elif risk_factor == 'high':
                risk_factor_value = 0.5
            elif risk_factor == 'critical':
                risk_factor_value = 1

        # Calculate the score for this vulnerability using the formula
        score = (ac / 5) * ae * risk_factor_value * epss * (cvss / 10) * (severity / 4)

        # Update the true risk score for this vulnerability directly in the database
        Vulnerability.objects.filter(pk=instance.pk).update(true_risk_score=score)
# Create your models here.
