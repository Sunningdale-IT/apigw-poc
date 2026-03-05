"""
Views for the Model Citizen application.
"""
import datetime
import re
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .decorators import login_required


def _rewrite_photo_urls(dog):
    """
    Replace any internal cluster hostname in photo URLs with the public
    DOGCATCHER_PUBLIC_URL so browsers can fetch the images.

    The dogcatcher serializer builds URLs from the Host header it receives,
    which is the internal Kong service name when called pod-to-pod.  We swap
    that out for the externally reachable hostname here.
    
    Also handles relative URLs by converting them to absolute URLs using
    DOGCATCHER_PUBLIC_URL.
    """
    public_base = settings.DOGCATCHER_PUBLIC_URL.rstrip('/')
    for field in ('photo_url', 'photo_download_url'):
        url = dog.get(field)
        if url:
            # If it's a relative URL (starts with /), prepend the public base
            if url.startswith('/'):
                dog[field] = public_base + url
            else:
                # Replace everything up to (but not including) the path component
                dog[field] = re.sub(r'^https?://[^/]+', public_base, url)
    return dog


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
        dogs = [_rewrite_photo_urls(d) for d in response.json()]
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
        'dogcatcher_url': settings.DOGCATCHER_PUBLIC_URL,
        'api_endpoint': f'{settings.API_GATEWAY_URL}/dogs/'
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
        dog = _rewrite_photo_urls(response.json())
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving dog details: {str(e)}'
    
    return render(request, 'found_dog_detail.html', {
        'citizen': citizen,
        'dog': dog,
        'error': error,
        'dogcatcher_url': settings.DOGCATCHER_PUBLIC_URL
    })


@login_required
def movies_view(request):
    """Movies showing at local cinemas."""
    citizen = get_citizen_info(request)
    movies = []
    error = None
    
    try:
        response = requests.get(f'{settings.MOVIEZZZ_URL}/api/movies/', timeout=5)
        response.raise_for_status()
        data = response.json()
        movies = data.get('results', data) if isinstance(data, dict) else data
    except requests.exceptions.ConnectionError:
        error = 'Unable to connect to the movies database. Please try again later.'
    except requests.exceptions.Timeout:
        error = 'The movies database is taking too long to respond. Please try again later.'
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving movies: {str(e)}'
    
    return render(request, 'movies.html', {
        'citizen': citizen,
        'movies': movies,
        'error': error,
        'moviezzz_url': settings.MOVIEZZZ_URL
    })


@login_required
def parking_view(request):
    """Available parking spots in the city."""
    citizen = get_citizen_info(request)
    spots = []
    error = None
    
    try:
        # Only show available spots
        response = requests.get(f'{settings.FREE_PARKING_URL}/api/spots/?available=true', timeout=5)
        response.raise_for_status()
        data = response.json()
        spots = data.get('results', data) if isinstance(data, dict) else data
    except requests.exceptions.ConnectionError:
        error = 'Unable to connect to the parking database. Please try again later.'
    except requests.exceptions.Timeout:
        error = 'The parking database is taking too long to respond. Please try again later.'
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving parking spots: {str(e)}'
    
    return render(request, 'parking.html', {
        'citizen': citizen,
        'spots': spots,
        'error': error,
        'parking_url': settings.FREE_PARKING_URL
    })


@login_required
def good_behaviour_view(request):
    """Search for a citizen's good behaviour record by ID."""
    citizen = get_citizen_info(request)
    citizen_data = None
    error = None
    error_title = None
    searched_id = None

    # Get citizen ID from POST or GET parameter
    if request.method == 'POST':
        searched_id = request.POST.get('citizen_id', '').strip().upper()
    else:
        searched_id = request.GET.get('citizen_id', '').strip().upper()

    # If a citizen ID was provided, look it up
    if searched_id:
        try:
            records_base = settings.GOOD_BEHAVIOUR_URL.rstrip('/')
            # Support both direct service URLs (..../api/citizens) and
            # gateway route URLs (..../good-behaviour) without double-prefixing.
            if records_base.endswith('/api/citizens') or records_base.endswith('/good-behaviour'):
                check_url = f'{records_base}/check/{searched_id}/'
            else:
                check_url = f'{records_base}/api/citizens/check/{searched_id}/'
            response = requests.get(check_url, timeout=5)
            response.raise_for_status()
            citizen_data = response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                error_title = 'Not Found'
                error = f'No citizen found with ID: {searched_id}. Try CIT001, CIT002, CIT003, or CIT-2001.'
            else:
                error_title = 'Service Error'
                error = f'Error checking Good Behaviour record: {str(e)}'
        except requests.exceptions.ConnectionError:
            error_title = 'Connection Issue'
            error = 'Unable to connect to the Good Behaviour service. Please try again later.'
        except requests.exceptions.Timeout:
            error_title = 'Timeout'
            error = 'The Good Behaviour service is taking too long to respond. Please try again later.'
        except requests.exceptions.RequestException as e:
            error_title = 'Service Error'
            error = f'Error retrieving Good Behaviour records: {str(e)}'

    return render(request, 'good_behaviour.html', {
        'citizen': citizen,
        'citizen_data': citizen_data,
        'searched_id': searched_id,
        'error': error,
        'error_title': error_title,
        'records_url': settings.GOOD_BEHAVIOUR_URL
    })


@login_required
def park_runs_view(request):
    """Saturday park run events."""
    citizen = get_citizen_info(request)
    park_runs = []
    error = None
    
    try:
        response = requests.get(f'{settings.PARK_RUNS_URL}/api/parkruns/', timeout=5)
        response.raise_for_status()
        data = response.json()
        park_runs = data.get('results', data) if isinstance(data, dict) else data
    except requests.exceptions.ConnectionError:
        error = 'Unable to connect to the park runs database. Please try again later.'
    except requests.exceptions.Timeout:
        error = 'The park runs database is taking too long to respond. Please try again later.'
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving park runs: {str(e)}'
    
    return render(request, 'park_runs.html', {
        'citizen': citizen,
        'park_runs': park_runs,
        'error': error,
        'park_runs_url': settings.PARK_RUNS_URL
    })

