from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q, Count
from datetime import datetime
from django.db.models.functions import TruncDate
import json

from vulnerabilities.models import Vulnerability
from analyst_file.models import AnalystFile
from vulnerabilities.utils import parse_vulnerability_xml

@login_required
def vulnerability_list_view(request):
    # Get filter parameters
    severity = request.GET.get('severity')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    analyst_id = request.GET.get('analyst')

    # Start with vulnerabilities for the logged-in user only
    vulnerabilities = Vulnerability.objects.filter(analyst=request.user)

    # Apply filters
    if severity:
        vulnerabilities = vulnerabilities.filter(severity=severity)

    if search:
        vulnerabilities = vulnerabilities.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) | 
            Q(cve__icontains=search) |
            Q(affected_asset__icontains=search)
        )

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            vulnerabilities = vulnerabilities.filter(discovered_date__gte=date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            vulnerabilities = vulnerabilities.filter(discovered_date__lte=date_to_obj)
        except ValueError:
            pass

    if analyst_id:
        vulnerabilities = vulnerabilities.filter(analyst_id=analyst_id)

    # Order by severity (descending) and discovered date
    vulnerabilities = vulnerabilities.order_by('-severity', 'discovered_date')

    # Paginate results
    paginator = Paginator(vulnerabilities, 10)  # Show 10 vulnerabilities per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vulnerabilities': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }

    return render(request, 'vulnerabilities/vulnerability_list.html', context)

@login_required
def vulnerability_detail_view(request, pk):
    # Only allow users to view their own vulnerabilities
    vulnerability = get_object_or_404(Vulnerability, pk=pk, analyst=request.user)
    return render(request, 'vulnerabilities/vulnerability_detail.html', {'vulnerability': vulnerability})

@login_required
@ensure_csrf_cookie
def import_vulnerabilities_view(request):
    file_id = request.GET.get('file_id') or request.POST.get('file_id')
    file = None
    imported_vulnerabilities = []
    error = None
    success = None

    if file_id:
        try:
            file = AnalystFile.objects.get(id=file_id, analyst=request.user)

            if request.method == 'POST':
                severity_threshold = int(request.POST.get('severity_threshold', 0))
                skip_duplicates = request.POST.get('skip_duplicates') == 'on'

                # Parse the XML file and create vulnerabilities based on the data in the file
                if file.is_xml:
                    try:
                        # Get the file path
                        file_path = file.upload.path

                        # Parse the XML file and create vulnerabilities
                        stats = parse_vulnerability_xml(file_path, request.user)

                        # Filter vulnerabilities based on severity threshold
                        if severity_threshold > 0:
                            # Get the most recently created vulnerabilities by this user
                            recent_vulns = Vulnerability.objects.filter(
                                analyst=request.user
                            ).order_by('-id')[:stats['created']]

                            # Filter out vulnerabilities below the threshold
                            for vuln in recent_vulns:
                                if vuln.severity >= severity_threshold:
                                    imported_vulnerabilities.append(vuln)
                                else:
                                    # Delete vulnerabilities below the threshold
                                    vuln.delete()

                            success = f"Successfully imported {len(imported_vulnerabilities)} vulnerabilities with severity >= {severity_threshold}."
                        else:
                            # Get all created vulnerabilities
                            imported_vulnerabilities = Vulnerability.objects.filter(
                                analyst=request.user
                            ).order_by('-id')[:stats['created']]

                            success = f"Successfully imported {stats['created']} vulnerabilities."

                        # Add additional information to success message if there were duplicates or errors
                        if stats['duplicates'] > 0:
                            success += f" {stats['duplicates']} duplicates were skipped."
                        if stats['errors'] > 0:
                            success += f" {stats['errors']} errors occurred during import."
                    except Exception as e:
                        error = f"Error parsing file: {str(e)}"
                else:
                    error = "The selected file is not in a supported format."

        except AnalystFile.DoesNotExist:
            error = "File not found or you don't have permission to access it."

    context = {
        'file': file,
        'imported_vulnerabilities': imported_vulnerabilities,
        'error': error,
        'success': success,
    }

    return render(request, 'vulnerabilities/import_vulnerabilities.html', context)

