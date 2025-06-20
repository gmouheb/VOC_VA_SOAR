from django.db import models 
from vulnerabilities.models import Vulnerability


class Asset(models.Model):
    asset_name = models.CharField(max_length=100)
    asset_type = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    asset_criticality = models.IntegerField()
    state = models.CharField(max_length=100,default="open")
    asset_true_risk_score = models.FloatField(null=True, blank=True)
    asset_exposure = models.BooleanField(default=False, help_text="If True (1), the asset is publicly exposed. If False (0), the asset is not publicly exposed.")
    vulnerabilities = models.ManyToManyField('vulnerabilities.Vulnerability',related_name='assets')
    owner = models.ForeignKey('analysts.Analyst',on_delete=models.CASCADE,related_name='assets')

    def __str__(self):
        return f'{self.asset_name} ({self.asset_type})'
    def calculate_true_risk_score(self):



        if not self.vulnerabilities.exists():
            return 0

        total_score = 0
        count = 0

        for vulnerability in self.vulnerabilities.all():

            cvss = vulnerability.cvss_score
            try:
                epss = float(vulnerability.epss) if vulnerability.epss else 1.0
            except ValueError:
                epss = 1.0


            ac = self.asset_criticality


            ae = 1.0 if self.asset_exposure else 0.5


            severity = vulnerability.severity


            risk_factor_value = 1.0  # Default value
            if vulnerability.risk_factor:
                risk_factor = vulnerability.risk_factor.lower()
                if risk_factor == 'low':
                    risk_factor_value = 0.15
                elif risk_factor == 'medium':
                    risk_factor_value = 0.25
                elif risk_factor == 'high':
                    risk_factor_value = 0.5
                elif risk_factor == 'critical':
                    risk_factor_value = 1


            score = (ac / 5) * ae * risk_factor_value * epss * (cvss / 10) * (severity / 4)


            # Update the true risk score for this vulnerability directly in the database
            # This avoids triggering the post_save signal and causing infinite recursion
            Vulnerability.objects.filter(pk=vulnerability.pk).update(true_risk_score=score)

            total_score += score
            count += 1


        return total_score / count if count > 0 else 0

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        if self.pk:
            self.asset_true_risk_score = self.calculate_true_risk_score()
            # Save again without triggering the full save method to avoid infinite recursion
            Asset.objects.filter(pk=self.pk).update(asset_true_risk_score=self.asset_true_risk_score)
