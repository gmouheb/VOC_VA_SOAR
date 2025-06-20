from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from assets.models import Asset
from vulnerabilities.models import Vulnerability

@login_required
def asset_list_view(request):
    # Get filter parameters
    asset_type = request.GET.get('asset_type')
    search = request.GET.get('search')
    criticality = request.GET.get('criticality')
    state = request.GET.get('state')

    # Start with assets for the logged-in user only
    assets = Asset.objects.filter(owner=request.user)

    # Apply filters
    if asset_type:
        assets = assets.filter(asset_type=asset_type)

    if search:
        assets = assets.filter(
            Q(asset_name__icontains=search) | 
            Q(company__icontains=search)
        )

    if criticality:
        assets = assets.filter(asset_criticality=criticality)

    if state:
        assets = assets.filter(state=state)

    # Order by asset_true_risk_score (descending) and asset_name
    assets = assets.order_by('-asset_true_risk_score', 'asset_name')

    # Paginate results
    paginator = Paginator(assets, 10)  # Show 10 assets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get unique asset types for filter dropdown
    asset_types = Asset.objects.filter(owner=request.user).values_list('asset_type', flat=True).distinct()

    context = {
        'assets': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'asset_types': asset_types,
    }

    return render(request, 'assets/asset_list.html', context)

@login_required
def asset_detail_view(request, pk):
    # Only allow users to view their own assets
    asset = get_object_or_404(Asset, pk=pk, owner=request.user)

    # Get vulnerabilities associated with this asset
    vulnerabilities = asset.vulnerabilities.all()

    context = {
        'asset': asset,
        'vulnerabilities': vulnerabilities,
    }

    return render(request, 'assets/asset_detail.html', context)

@login_required
def create_asset_view(request):
    if request.method == 'POST':
        asset_name = request.POST.get('asset_name')
        asset_type = request.POST.get('asset_type')
        company = request.POST.get('company')
        asset_criticality = request.POST.get('asset_criticality')
        state = request.POST.get('state')
        asset_exposure = request.POST.get('asset_exposure') == 'on'

        # Validate input
        errors = {}
        if not asset_name:
            errors['asset_name'] = ['This field is required.']
        if not asset_type:
            errors['asset_type'] = ['This field is required.']
        if not company:
            errors['company'] = ['This field is required.']
        if not asset_criticality:
            errors['asset_criticality'] = ['This field is required.']
        if not state:
            errors['state'] = ['This field is required.']

        # Validate asset_criticality is a number between 1 and 5
        try:
            asset_criticality = int(asset_criticality)
            if asset_criticality < 1 or asset_criticality > 5:
                errors['asset_criticality'] = ['Criticality must be between 1 and 5.']
        except (ValueError, TypeError):
            errors['asset_criticality'] = ['Criticality must be a number.']

        if errors:
            return render(request, 'assets/asset_form.html', {'errors': errors})

        # Create asset
        asset = Asset(
            asset_name=asset_name,
            asset_type=asset_type,
            company=company,
            asset_criticality=asset_criticality,
            state=state,
            asset_exposure=asset_exposure,
            owner=request.user
        )
        asset.save()

        messages.success(request, 'Asset created successfully!')
        return redirect('asset_detail', pk=asset.id)

    return render(request, 'assets/asset_form.html')

@login_required
def edit_asset_view(request, pk):
    # Only allow users to edit their own assets
    asset = get_object_or_404(Asset, pk=pk, owner=request.user)

    if request.method == 'POST':
        asset_name = request.POST.get('asset_name')
        asset_type = request.POST.get('asset_type')
        company = request.POST.get('company')
        asset_criticality = request.POST.get('asset_criticality')
        state = request.POST.get('state')
        asset_exposure = request.POST.get('asset_exposure') == 'on'

        # Validate input
        errors = {}
        if not asset_name:
            errors['asset_name'] = ['This field is required.']
        if not asset_type:
            errors['asset_type'] = ['This field is required.']
        if not company:
            errors['company'] = ['This field is required.']
        if not asset_criticality:
            errors['asset_criticality'] = ['This field is required.']
        if not state:
            errors['state'] = ['This field is required.']

        # Validate asset_criticality is a number between 1 and 5
        try:
            asset_criticality = int(asset_criticality)
            if asset_criticality < 1 or asset_criticality > 5:
                errors['asset_criticality'] = ['Criticality must be between 1 and 5.']
        except (ValueError, TypeError):
            errors['asset_criticality'] = ['Criticality must be a number.']

        if errors:
            return render(request, 'assets/asset_form.html', {'errors': errors, 'asset': asset})

        # Update asset
        asset.asset_name = asset_name
        asset.asset_type = asset_type
        asset.company = company
        asset.asset_criticality = asset_criticality
        asset.state = state
        asset.asset_exposure = asset_exposure
        asset.save()

        messages.success(request, 'Asset updated successfully!')
        return redirect('asset_detail', pk=asset.id)

    return render(request, 'assets/asset_form.html', {'asset': asset})
