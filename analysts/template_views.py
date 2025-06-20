from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import os

from analysts.models import Analyst, APIKey
from vulnerabilities.models import Vulnerability
from analyst_file.models import AnalystFile

def landing_page_view(request):
    """
    View for the landing page.
    """
    return render(request, 'index.html')

@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = Analyst.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'analysts/login.html', {'error': 'Invalid email or password'})
        except Analyst.DoesNotExist:
            return render(request, 'analysts/login.html', {'error': 'Invalid email or password'})

    return render(request, 'analysts/login.html')

@ensure_csrf_cookie
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        company = request.POST.get('company')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Validate input
        errors = {}
        if not first_name:
            errors['first_name'] = ['This field is required.']
        if not last_name:
            errors['last_name'] = ['This field is required.']
        if not email:
            errors['email'] = ['This field is required.']
        if not company:
            errors['company'] = ['This field is required.']
        if not password:
            errors['password'] = ['This field is required.']
        if password != password_confirm:
            errors['password_confirm'] = ['Passwords do not match.']

        # Check if email already exists
        if Analyst.objects.filter(email=email).exists():
            errors['email'] = ['Email already exists.']

        if errors:
            return render(request, 'analysts/register.html', {'errors': errors})

        # Create user
        user = Analyst.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            company=company
        )

        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('dashboard')

    return render(request, 'analysts/register.html')

@login_required
def logout_view(request):
    # Get all files uploaded by the current user
    user_files = AnalystFile.objects.filter(analyst=request.user)

    # Delete physical files and database records
    for file in user_files:
        # Delete the physical file if it exists
        if file.upload and hasattr(file.upload, 'path') and os.path.exists(file.upload.path):
            try:
                os.remove(file.upload.path)
            except (OSError, PermissionError) as e:
                print(f"Error deleting file {file.upload.path}: {e}")

    # Delete all file records for this user
    user_files.delete()

    # Delete all files in media/analyst_file directory
    import shutil
    analyst_file_dir = os.path.join('media', 'analyst_file')
    if os.path.exists(analyst_file_dir) and os.path.isdir(analyst_file_dir):
        for filename in os.listdir(analyst_file_dir):
            file_path = os.path.join(analyst_file_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

    # Logout the user
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'analysts/profile.html')

@login_required
@ensure_csrf_cookie
def edit_profile_view(request):
    user = request.user

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        company = request.POST.get('company')

        # Validate input
        errors = {}
        if not first_name:
            errors['first_name'] = ['This field is required.']
        if not last_name:
            errors['last_name'] = ['This field is required.']
        if not email:
            errors['email'] = ['This field is required.']
        if not company:
            errors['company'] = ['This field is required.']

        # Check if email already exists (excluding current user)
        if Analyst.objects.filter(email=email).exclude(id=user.id).exists():
            errors['email'] = ['Email already exists.']

        if errors:
            return render(request, 'analysts/edit_profile.html', {'errors': errors})

        # Update user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.company = company
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'analysts/edit_profile.html')

@login_required
@ensure_csrf_cookie
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate input
        if not request.user.check_password(current_password):
            return render(request, 'analysts/change_password.html', {'error': 'Current password is incorrect.'})

        if new_password != confirm_password:
            return render(request, 'analysts/change_password.html', {'error': 'New passwords do not match.'})

        # Update password
        request.user.set_password(new_password)
        request.user.save()

        # Re-login the user
        login(request, request.user)

        return render(request, 'analysts/change_password.html', {'success': 'Password changed successfully!'})

    return render(request, 'analysts/change_password.html')

@login_required
def dashboard_view(request):
    # Get vulnerability counts by severity for the logged-in user only
    critical_count = Vulnerability.objects.filter(severity=4, analyst=request.user).count()
    high_count = Vulnerability.objects.filter(severity=3, analyst=request.user).count()
    medium_count = Vulnerability.objects.filter(severity=2, analyst=request.user).count()
    low_count = Vulnerability.objects.filter(severity=1, analyst=request.user).count()
    info_count = Vulnerability.objects.filter(severity=0, analyst=request.user).count()

    # Get recent vulnerabilities for the logged-in user only
    recent_vulnerabilities = Vulnerability.objects.filter(analyst=request.user).order_by('-created_at')[:5]

    # Get recent files
    recent_files = AnalystFile.objects.filter(analyst=request.user).order_by('-created_at')[:5]

    # Get visualization data
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    import json
    from django.core.serializers.json import DjangoJSONEncoder

    # 1. Affected Assets Over Time for the logged-in user only
    assets_over_time = Vulnerability.objects.filter(analyst=request.user).annotate(
        date=TruncDate('discovered_date')
    ).values('date').annotate(
        count=Count('affected_asset', distinct=True)
    ).order_by('date')

    # Convert date objects to strings for JSON serialization
    assets_over_time_list = []
    for item in assets_over_time:
        assets_over_time_list.append({
            'date': item['date'].strftime('%Y-%m-%d') if item['date'] else '',
            'count': item['count']
        })

    # 2. Highest Vulnerabilities (Top 10) for the logged-in user only
    highest_vulnerabilities = Vulnerability.objects.filter(analyst=request.user).values('name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # 3. Severity Distribution for the logged-in user only
    severity_distribution = Vulnerability.objects.filter(analyst=request.user).values('severity').annotate(
        count=Count('id')
    ).order_by('severity')

    # Convert severity numbers to labels
    severity_labels = dict(Vulnerability.SEVERITY_CHOICES)
    severity_distribution_list = []
    for item in severity_distribution:
        severity_distribution_list.append({
            'label': severity_labels.get(item['severity'], 'Unknown'),
            'count': item['count'],
            'severity': item['severity']
        })

    # 4. Most Affected Assets (Top 10) for the logged-in user only
    most_affected_assets = Vulnerability.objects.filter(analyst=request.user).values('affected_asset').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    context = {
        'critical_count': critical_count,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'info_count': info_count,
        'recent_vulnerabilities': recent_vulnerabilities,
        'recent_files': recent_files,
        'assets_over_time': json.dumps(assets_over_time_list, cls=DjangoJSONEncoder),
        'highest_vulnerabilities': json.dumps(list(highest_vulnerabilities), cls=DjangoJSONEncoder),
        'severity_distribution': json.dumps(severity_distribution_list, cls=DjangoJSONEncoder),
        'most_affected_assets': json.dumps(list(most_affected_assets), cls=DjangoJSONEncoder),
    }

    return render(request, 'dashboard.html', context)

@login_required
@ensure_csrf_cookie
def api_key_management_view(request):
    """
    View for managing API keys.
    """
    # Get all API keys for the current user
    api_keys = APIKey.objects.filter(analyst=request.user).order_by('-created_at')

    # Handle API key generation
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate':
            # Generate a new API key
            name = request.POST.get('name', f"API Key {len(api_keys) + 1}")
            api_key = APIKey.objects.create(
                name=name,
                analyst=request.user
            )
            # Pass the newly created key to the template for display
            context = {
                'api_keys': APIKey.objects.filter(analyst=request.user).order_by('-created_at'),
                'new_key': api_key
            }
            return render(request, 'analysts/api_key_management.html', context)

        elif action == 'delete':
            # Delete an API key
            key_id = request.POST.get('key_id')
            try:
                api_key = APIKey.objects.get(id=key_id, analyst=request.user)
                name = api_key.name
                api_key.delete()
                messages.success(request, f'API key "{name}" deleted successfully.')
            except APIKey.DoesNotExist:
                messages.error(request, 'API key not found.')
            return redirect('api_key_management')

    context = {
        'api_keys': api_keys
    }

    return render(request, 'analysts/api_key_management.html', context)
