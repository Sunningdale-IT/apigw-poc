"""
Views for the Model Citizen application.
"""
import datetime
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settingsfrom django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .decorators import login_required


@csrf_exempt
def health(request):
    """Health check endpoint for Kubernetes probes."""
    return JsonResponse({'status': 'healthy', 'service': 'model-citizen'})


def get_citizen_info(request):
    """Get current logged in citizen info."""
    citizen_id = request.session.get('citizen_id')
    if citizen_id and citizen_id in settings.MOCK_CITIZENS:
        return {'id': citizen_id, **settings.MOCK_CITIZENS[citizen_id]}
    return None


def index(request):
    """Landing page - redirect to login or dashboard."""
    if 'citizen_id' in request.session:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    """CitID Login page."""
    if request.method == 'POST':
        citizen_id = request.POST.get('citizen_id', '').strip().upper()
        
        if citizen_id in settings.MOCK_CITIZENS:
            request.session['citizen_id'] = citizen_id
            messages.success(request, f'Welcome back, {settings.MOCK_CITIZENS[citizen_id]["name"]}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid CitID. Please try again.')
    
    return render(request, 'login.html')


def logout_view(request):
    """Logout and clear session."""
    request.session.flush()
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard with all services."""
    citizen = get_citizen_info(request)
    return render(request, 'dashboard.html', {'citizen': citizen})


@login_required
def passport(request):
    """Passport renewal service (mocked)."""
    citizen = get_citizen_info(request)
    
    if request.method == 'POST':
        messages.success(request, 'Passport renewal request submitted successfully! Your new passport will arrive in 4-6 weeks.')
        return redirect('passport')
    
    passport_data = {
        'number': 'P' + citizen['id'] + '12345',
        'issue_date': '2020-03-15',
        'expiry_date': '2030-03-14',
        'status': 'Valid'
    }
    
    return render(request, 'passport.html', {'citizen': citizen, 'passport': passport_data})


@login_required
def driving_license(request):
    """Driving license renewal service (mocked)."""
    citizen = get_citizen_info(request)
    
    if request.method == 'POST':
        messages.success(request, 'Driving license renewal request submitted! Your new license will be mailed within 10 business days.')
        return redirect('driving_license')
    
    license_data = {
        'number': 'DL' + citizen['id'] + '98765',
        'license_class': 'B',
        'issue_date': '2019-06-20',
        'expiry_date': '2029-06-19',
        'status': 'Valid',
        'points': 0
    }
    
    return render(request, 'driving_license.html', {'citizen': citizen, 'license': license_data})


@login_required
def building_permit(request):
    """Building permit application (mocked)."""
    citizen = get_citizen_info(request)
    
    if request.method == 'POST':
        permit_number = 'BP' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        messages.success(request, f'Building permit application submitted! Reference number: {permit_number}. You will receive a decision within 30 days.')
        return redirect('building_permit')
    
    permits = [
        {'number': 'BP20250115001', 'type': 'Extension', 'status': 'Approved', 'date': '2025-01-15'},
        {'number': 'BP20240820002', 'type': 'Renovation', 'status': 'Completed', 'date': '2024-08-20'},
    ]
    
    return render(request, 'building_permit.html', {'citizen': citizen, 'permits': permits})


@login_required
def trash_collection(request):
    """Trash collection information (mocked)."""
    citizen = get_citizen_info(request)
    
    schedule = {
        'general_waste': 'Monday',
        'recycling': 'Wednesday',
        'garden_waste': 'Friday (Apr-Oct)',
        'bulk_collection': 'First Saturday of month (by appointment)'
    }
    
    today = datetime.date.today()
    upcoming = []
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for i in range(14):
        date = today + datetime.timedelta(days=i)
        day_name = days[date.weekday()]
        
        if day_name == 'Monday':
            upcoming.append({'date': date.strftime('%Y-%m-%d'), 'day': day_name, 'type': 'General Waste', 'icon': 'trash'})
        elif day_name == 'Wednesday':
            upcoming.append({'date': date.strftime('%Y-%m-%d'), 'day': day_name, 'type': 'Recycling', 'icon': 'recycle'})
        elif day_name == 'Friday':
            upcoming.append({'date': date.strftime('%Y-%m-%d'), 'day': day_name, 'type': 'Garden Waste', 'icon': 'leaf'})
    
    return render(request, 'trash_collection.html', {'citizen': citizen, 'schedule': schedule, 'upcoming': upcoming})


@login_required
def found_dogs(request):
    """Found dogs - integrates with Dogcatcher API via API Gateway."""
    citizen = get_citizen_info(request)
    dogs = []
    error = None
    
    try:
        headers = {}
        if settings.DOGCATCHER_API_KEY:
            headers['X-API-Key'] = settings.DOGCATCHER_API_KEY
        
        response = requests.get(f'{settings.API_GATEWAY_URL}/dogs/', headers=headers, timeout=5)
        response.raise_for_status()
        dogs = response.json()
    except requests.exceptions.ConnectionError:
        error = 'Unable to connect to the Dog Pound database. Please try again later.'
    except requests.exceptions.Timeout:
        error = 'The Dog Pound database is taking too long to respond. Please try again later.'
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving found dogs: {str(e)}'
    
    return render(request, 'found_dogs.html', {
        'citizen': citizen,
        'dogs': dogs,
        'error': error,
        'dogcatcher_url': settings.DOGCATCHER_PUBLIC_URL
    })


@login_required
def found_dog_detail(request, dog_id):
    """Individual dog detail page."""
    citizen = get_citizen_info(request)
    dog = None
    error = None
    
    try:
        headers = {}
        if settings.DOGCATCHER_API_KEY:
            headers['X-API-Key'] = settings.DOGCATCHER_API_KEY
        
        response = requests.get(f'{settings.API_GATEWAY_URL}/dogs/{dog_id}/', headers=headers, timeout=5)
        response.raise_for_status()
        dog = response.json()
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving dog details: {str(e)}'
    
    return render(request, 'found_dog_detail.html', {
        'citizen': citizen,
        'dog': dog,
        'error': error,
        'dogcatcher_url': settings.DOGCATCHER_PUBLIC_URL
    })
