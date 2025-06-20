import os
import xml.etree.ElementTree as ET
from datetime import datetime
from .models import Vulnerability  # Adjust if needed


def get_element_text(element, xpath):
    """
    Safely get the text content of a subelement from an XML element.
    """
    try:
        found = element.find(xpath)
        return found.text.strip() if found is not None and found.text else None
    except Exception:
        return None


def normalize_severity(severity):
    """
    Normalize severity to a numeric value (0–4) regardless of input format.
    """
    if isinstance(severity, int) and 0 <= severity <= 4:
        return severity

    if isinstance(severity, str):
        severity = severity.lower().strip()

        if severity in ['4', 'critical', 'severe', 'important']:
            return 4
        elif severity in ['3', 'high']:
            return 3
        elif severity in ['2', 'medium', 'moderate', 'warning']:
            return 2
        elif severity in ['1', 'low']:
            return 1
        elif severity in ['0', 'info', 'information', 'informational', 'informative']:
            return 0

    return 2  # Default to Medium


def parse_vulnerability_xml(file_path, analyst):
    """
    Parse a Nessus XML file and store vulnerabilities into the database.

    Args:
        file_path (str): Path to the Nessus XML file.
        analyst: Analyst object (ForeignKey on Vulnerability)

    Returns:
        dict: Stats about processed vulnerabilities.
    """
    print(f"Parsing file: {file_path}")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    stats = {
        'total_found': 0,
        'processed': 0,
        'created': 0,
        'skipped': 0,
        'duplicates': 0,
        'errors': 0,
        'error_details': [],
        'xml_structure': {}
    }

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        stats['xml_structure']['root_tag'] = root.tag
        child_tags = [child.tag for child in root]
        stats['xml_structure']['child_tags'] = child_tags[:10]

        if root.tag == 'NessusClientData_v2' or any(tag == 'Report' for tag in child_tags):
            print("Detected Nessus format")
            vulnerabilities = []

            for host in root.findall('.//ReportHost'):
                hostname = host.get('name', 'N/A')
                for item in host.findall('./ReportItem'):
                    vulnerabilities.append((item, hostname))

            stats['total_found'] = len(vulnerabilities)
            print(f"Found {len(vulnerabilities)} vulnerabilities")

            for index, (vuln, hostname) in enumerate(vulnerabilities):
                try:
                    stats['processed'] += 1
                    plugin_id = vuln.get('pluginID', '0')
                    vuln_name = vuln.get('pluginName', 'N/A')
                    if plugin_id == '0' or vuln_name == 'N/A':
                        stats['skipped'] += 1
                        continue

                    # Check if this exact vulnerability (same plugin_id, port, protocol, and hostname) already exists in the database
                    port = vuln.get('port', 'N/A')
                    protocol = vuln.get('protocol', 'N/A')

                    if Vulnerability.objects.filter(
                        name=hostname[:255],
                        port=port,
                        protocol=protocol,
                        description__contains=vuln_name,
                        analyst=analyst
                    ).exists():
                        stats['duplicates'] += 1
                        continue
                    severity = normalize_severity(vuln.get('severity', '0'))

                    # Get description and prepend vulnerability name
                    base_description = get_element_text(vuln, 'description') or \
                                      get_element_text(vuln, 'plugin_output') or \
                                      f"Plugin ID: {plugin_id}"
                    description = f"Vulnerability: {vuln_name}\n\n{base_description}"

                    solution = get_element_text(vuln, 'solution') or "N/A"
                    risk_factor = get_element_text(vuln, 'risk_factor') or "N/A"

                    see_also = ", ".join(
                        [e.text for e in vuln.findall('see_also') if e.text]
                    ) or "N/A"

                    xref = ", ".join(
                        [e.text for e in vuln.findall('xref') if e.text]
                    ) or "N/A"

                    epss_score = get_element_text(vuln, 'epss_score') or \
                                 get_element_text(vuln, 'epss') or "N/A"

                    cves = [e.text.strip() for e in vuln.findall('cve') if e.text]
                    if not cves:
                        stats['skipped'] += 1
                        continue

                    affected_asset = f"{hostname} ({port}/{protocol})"

                    for cve in cves:

                        vuln_obj = Vulnerability.objects.create(
                            name=hostname[:255],  # Use hostname/IP as name
                            port=port,
                            protocol=protocol,
                            description=description,
                            severity=severity,
                            cvss_score=float(vuln.findtext('cvss_base_score') or 5.0),
                            cve=cve,
                            affected_asset=affected_asset[:255],
                            remediation=solution,
                            risk_factor=risk_factor,
                            see_also=see_also,
                            xref=xref,
                            epss=epss_score,
                            discovered_date=datetime.now().date(),
                            analyst=analyst
                        )
                        print(f"Created Vulnerability: {vuln_obj.id}")
                        stats['created'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append(f"Error at index {index+1}: {str(e)}")

        else:
            stats['errors'] += 1
            stats['error_details'].append("Unsupported XML format")

    except Exception as e:
        raise Exception(f"Failed to parse XML: {str(e)}")

    print("Parsing complete.")
    return stats
