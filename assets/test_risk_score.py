#!/usr/bin/env python
"""
Test script for the asset_true_risk_score calculation.
Run this script with:
python manage.py shell < assets/test_risk_score.py
"""

from assets.models import Asset
from vulnerabilities.models import Vulnerability
from analysts.models import Analyst
from django.db import transaction

def test_risk_score_calculation():
    print("Testing asset_true_risk_score calculation...")
    print("This test will create a test asset with two vulnerabilities and calculate the true risk score.")

    # Get or create an analyst for testing
    try:
        analyst = Analyst.objects.first()
        if not analyst:
            print("No analysts found. Please create an analyst first.")
            return
    except Exception as e:
        print(f"Error getting analyst: {e}")
        return

    # Create a test asset
    try:
        with transaction.atomic():
            asset = Asset.objects.create(
                asset_name="Test Asset",
                asset_type="Server",
                company="Test Company",
                asset_criticality=3,  # AC value
                state="open",
                owner=analyst
            )
            print(f"Created test asset: {asset.asset_name}")

            # Create test vulnerabilities
            vuln1 = Vulnerability.objects.create(
                name="Test Vulnerability 1",
                description="Test description 1",
                severity=3,  # High
                cvss_score=7.5,
                epss="0.5",
                risk_factor="High",
                affected_asset="Test Asset",
                remediation="Test remediation",
                discovered_date="2023-01-01",
                analyst=analyst
            )

            vuln2 = Vulnerability.objects.create(
                name="Test Vulnerability 2",
                description="Test description 2",
                severity=2,  # Medium
                cvss_score=5.0,
                epss="0.3",
                risk_factor="Medium",
                affected_asset="Test Asset",
                remediation="Test remediation",
                discovered_date="2023-01-01",
                analyst=analyst
            )

            # Add vulnerabilities to the asset
            asset.vulnerabilities.add(vuln1, vuln2)

            # Calculate the expected score for vuln1
            # True Risk Score = AC/5 * AE * RF * EL * AS/10 * SEV/4
            # asset_exposure is 0.5 by default (False)
            expected_score1 = (3/5) * 0.5 * 0.5 * 0.5 * (7.5/10) * (3/4)  # High risk_factor = 0.5, asset_exposure = 0.5, severity = 3

            # Calculate the expected score for vuln2
            expected_score2 = (3/5) * 0.5 * 0.25 * 0.3 * (5.0/10) * (2/4)  # Medium risk_factor = 0.25, asset_exposure = 0.5, severity = 2

            # Calculate the expected average
            expected_avg = (expected_score1 + expected_score2) / 2

            # Force recalculation
            asset.asset_true_risk_score = asset.calculate_true_risk_score()
            Asset.objects.filter(pk=asset.pk).update(asset_true_risk_score=asset.asset_true_risk_score)

            # Refresh from database
            asset.refresh_from_db()

            print(f"Vulnerability 1 expected score: {expected_score1}")
            print(f"Vulnerability 2 expected score: {expected_score2}")
            print(f"Expected average score: {expected_avg}")
            print(f"Actual asset_true_risk_score: {asset.asset_true_risk_score}")

            # Clean up
            asset.delete()
            vuln1.delete()
            vuln2.delete()

            print("Test completed and test data cleaned up.")

    except Exception as e:
        print(f"Error during test: {e}")

# Always run the test when this script is executed
print("Starting test...")
test_risk_score_calculation()
print("Test completed.")
