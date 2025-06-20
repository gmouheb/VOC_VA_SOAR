import os
from django.conf import settings
from django.shortcuts import render
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import Vulnerability
from .serializers import VulnerabilitySerializer, VulnerabilityAPISerializer
# Make sure we're importing the latest version of the function
from .utils import parse_vulnerability_xml, normalize_severity, get_element_text
from analyst_file.models import AnalystFile

class VulnerabilityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows vulnerabilities to be viewed or edited.
    """
    serializer_class = VulnerabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'affected_asset', 'severity']
    ordering_fields = ['id', 'name', 'severity', 'cvss_score', 'discovered_date']

    def get_queryset(self):
        """
        This view returns vulnerabilities for the currently authenticated user
        unless the user is staff, in which case all vulnerabilities are returned.
        Also handles manual filtering through query parameters.
        Only vulnerabilities with CVE available are returned.
        """
        user = self.request.user
        queryset = Vulnerability.objects.all() if user.is_staff else Vulnerability.objects.filter(analyst=user)

        # Filter out vulnerabilities without CVE
        queryset = queryset.exclude(cve__isnull=True).exclude(cve="")

        # Manual filtering implementation
        severity = self.request.query_params.get('severity', None)
        if severity:
            queryset = queryset.filter(severity=severity)

        min_cvss = self.request.query_params.get('min_cvss', None)
        if min_cvss:
            queryset = queryset.filter(cvss_score__gte=float(min_cvss))

        max_cvss = self.request.query_params.get('max_cvss', None)
        if max_cvss:
            queryset = queryset.filter(cvss_score__lte=float(max_cvss))

        discovered_after = self.request.query_params.get('discovered_after', None)
        if discovered_after:
            queryset = queryset.filter(discovered_date__gte=discovered_after)

        discovered_before = self.request.query_params.get('discovered_before', None)
        if discovered_before:
            queryset = queryset.filter(discovered_date__lte=discovered_before)

        analyst_id = self.request.query_params.get('analyst', None)
        if analyst_id and user.is_staff:  # Only staff can filter by analyst
            queryset = queryset.filter(analyst_id=analyst_id)

        return queryset

    def perform_create(self, serializer):
        """Save the vulnerability with the current user as analyst"""
        serializer.save(analyst=self.request.user)


class ImportVulnerabilitiesView(APIView):
    """
    API endpoint to import vulnerabilities from an uploaded XML file.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Process XML file and import vulnerabilities
        """
        # Get file ID from request, if provided
        file_id = request.data.get('file_id')
        results = []
        total_created = 0
        success = True
        error_message = None

        try:
            if file_id:
                # Process specific file
                try:
                    print(f"Processing file with ID: {file_id}")
                    analyst_file = AnalystFile.objects.get(id=file_id, analyst=request.user)
                    print(f"Found file: {analyst_file.filename}, upload path: {analyst_file.upload}")

                    # Get absolute path to the file using the file field's path property
                    file_path = analyst_file.upload.path
                    print(f"File path resolved to: {file_path}")

                    # Check if file exists
                    if not os.path.exists(file_path):
                        print(f"File not found at path: {file_path}")
                        return Response({
                            'message': 'Error processing file',
                            'error': f'File not found: {file_path}',
                        }, status=status.HTTP_404_NOT_FOUND)

                    # Process the file
                    print(f"Starting to parse file: {file_path}")
                    print("Will import all vulnerabilities from the file")

                    # Process all vulnerabilities in the file
                    stats = parse_vulnerability_xml(file_path, request.user)
                    print(f"Parsing complete. Stats: {stats}")

                    total_created += stats['created']
                    results.append({
                        'file': analyst_file.filename,
                        'stats': stats
                    })

                except AnalystFile.DoesNotExist:
                    success = False
                    error_message = f'File with ID {file_id} not found or you do not have permission to access it.'
                    return Response({
                        'message': 'Error processing file',
                        'error': error_message,
                    }, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    success = False
                    error_message = str(e)
                    print(f"Error processing file ID {file_id}: {error_message}")
                    return Response({
                        'message': 'Error processing file',
                        'error': error_message,
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # Process all files for the user
                analyst_files = AnalystFile.objects.filter(analyst=request.user)

                if not analyst_files.exists():
                    return Response({
                        'message': 'No files found',
                        'error': 'No files found for the current user.',
                    }, status=status.HTTP_404_NOT_FOUND)

                print(f"Found {analyst_files.count()} files to process")

                for analyst_file in analyst_files:
                    try:
                        print(f"Processing file: {analyst_file.filename}, ID: {analyst_file.id}")
                        # Get absolute path to the file using the file field's path property
                        file_path = analyst_file.upload.path
                        print(f"File path resolved to: {file_path}")

                        # Skip if file doesn't exist
                        if not os.path.exists(file_path):
                            print(f"File not found at path: {file_path}")
                            results.append({
                                'file': analyst_file.filename,
                                'error': 'File not found on disk'
                            })
                            continue

                        # Check if file is XML
                        is_xml = (
                            analyst_file.type.lower() in ['text/xml', 'application/xml'] or 
                            analyst_file.filename.lower().endswith('.xml')
                        )
                        print(f"Is file XML? {is_xml}, Type: {analyst_file.type}, Filename: {analyst_file.filename}")

                        # Skip if not XML file
                        if not is_xml:
                            results.append({
                                'file': analyst_file.filename,
                                'error': 'Not an XML file'
                            })
                            continue

                        # Process the file
                        print(f"Starting to parse file: {file_path}")

                        # Process all vulnerabilities in the file
                        stats = parse_vulnerability_xml(file_path, request.user)
                        print(f"Parsing complete. Stats: {stats}")

                        total_created += stats['created']
                        results.append({
                            'file': analyst_file.filename,
                            'stats': stats
                        })

                    except Exception as e:
                        print(f"Error processing file {analyst_file.filename}: {str(e)}")
                        results.append({
                            'file': analyst_file.filename,
                            'error': str(e)
                        })

            # Determine if the operation was successful
            if total_created > 0:
                message = f"Data saved successfully. {total_created} vulnerabilities created."
            else:
                message = "No vulnerabilities were imported. Check the file format."

            return Response({
                'message': message,
                'success': success,
                'results': results,
                'total_files_processed': len(results),
                'total_vulnerabilities_created': total_created
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Unexpected error in import process: {str(e)}")
            return Response({
                'message': 'Error during import process',
                'error': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_vulnerabilities_json(request):
    """
    API endpoint that returns vulnerabilities for the currently authenticated user in JSON format.
    """
    user = request.user

    # Filter vulnerabilities by the logged-in user
    # Only include vulnerabilities with CVE available
    vulnerabilities = Vulnerability.objects.filter(analyst=user).exclude(cve__isnull=True).exclude(cve="")

    # Apply optional filters if provided in query parameters
    severity = request.query_params.get('severity', None)
    if severity:
        vulnerabilities = vulnerabilities.filter(severity=severity)

    min_cvss = request.query_params.get('min_cvss', None)
    if min_cvss:
        vulnerabilities = vulnerabilities.filter(cvss_score__gte=float(min_cvss))

    max_cvss = request.query_params.get('max_cvss', None)
    if max_cvss:
        vulnerabilities = vulnerabilities.filter(cvss_score__lte=float(max_cvss))

    discovered_after = request.query_params.get('discovered_after', None)
    if discovered_after:
        vulnerabilities = vulnerabilities.filter(discovered_date__gte=discovered_after)

    discovered_before = request.query_params.get('discovered_before', None)
    if discovered_before:
        vulnerabilities = vulnerabilities.filter(discovered_date__lte=discovered_before)

    # Serialize the vulnerabilities
    serializer = VulnerabilitySerializer(vulnerabilities, many=True)

    # Return the serialized data as JSON
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_vulnerabilities_api(request):
    """
    API endpoint that returns all vulnerabilities with all columns except analyst,
    and includes the true_risk_score.
    """
    # Get all vulnerabilities
    vulnerabilities = Vulnerability.objects.all()

    # Apply optional filters if provided in query parameters
    severity = request.query_params.get('severity', None)
    if severity:
        vulnerabilities = vulnerabilities.filter(severity=severity)

    min_cvss = request.query_params.get('min_cvss', None)
    if min_cvss:
        vulnerabilities = vulnerabilities.filter(cvss_score__gte=float(min_cvss))

    max_cvss = request.query_params.get('max_cvss', None)
    if max_cvss:
        vulnerabilities = vulnerabilities.filter(cvss_score__lte=float(max_cvss))

    discovered_after = request.query_params.get('discovered_after', None)
    if discovered_after:
        vulnerabilities = vulnerabilities.filter(discovered_date__gte=discovered_after)

    discovered_before = request.query_params.get('discovered_before', None)
    if discovered_before:
        vulnerabilities = vulnerabilities.filter(discovered_date__lte=discovered_before)

    # Serialize the vulnerabilities using the API serializer
    serializer = VulnerabilityAPISerializer(vulnerabilities, many=True)

    # Return the serialized data as JSON
    return Response(serializer.data)
