import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'citizen-secret-key-change-in-production')

# API Gateway URL - points to Kong which proxies to Dogcatcher
# In Kubernetes: http://kong-proxy.kong.svc.cluster.local/dogcatcher/api
# In Docker Compose: http://kong:8000/dogcatcher/api
API_GATEWAY_URL = os.environ.get('API_GATEWAY_URL', 'http://kong:8000/dogcatcher/api')

# Mock citizen database
MOCK_CITIZENS = {
    'CIT001': {'name': 'John Smith', 'email': 'john.smith@email.com', 'address': '123 Main Street, Springfield'},
    'CIT002': {'name': 'Jane Doe', 'email': 'jane.doe@email.com', 'address': '456 Oak Avenue, Riverside'},
    'CIT003': {'name': 'Bob Wilson', 'email': 'bob.wilson@email.com', 'address': '789 Pine Road, Lakeside'},
    'DEMO': {'name': 'Demo User', 'email': 'demo@example.com', 'address': '1 Demo Lane, Test City'},
}


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'citizen_id' not in session:
            flash('Please log in to access this service.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_citizen_info():
    """Get current logged in citizen info"""
    citizen_id = session.get('citizen_id')
    if citizen_id and citizen_id in MOCK_CITIZENS:
        return {'id': citizen_id, **MOCK_CITIZENS[citizen_id]}
    return None


@app.route('/')
def index():
    """Landing page - redirect to login or dashboard"""
    if 'citizen_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """CitID Login page"""
    if request.method == 'POST':
        citizen_id = request.form.get('citizen_id', '').strip().upper()
        
        if citizen_id in MOCK_CITIZENS:
            session['citizen_id'] = citizen_id
            flash(f'Welcome back, {MOCK_CITIZENS[citizen_id]["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid CitID. Please try again.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with all services"""
    citizen = get_citizen_info()
    return render_template('dashboard.html', citizen=citizen)


@app.route('/passport', methods=['GET', 'POST'])
@login_required
def passport():
    """Passport renewal service (mocked)"""
    citizen = get_citizen_info()
    
    if request.method == 'POST':
        # Mock passport renewal
        flash('Passport renewal request submitted successfully! Your new passport will arrive in 4-6 weeks.', 'success')
        return redirect(url_for('passport'))
    
    # Mock passport data
    passport_data = {
        'number': 'P' + citizen['id'] + '12345',
        'issue_date': '2020-03-15',
        'expiry_date': '2030-03-14',
        'status': 'Valid'
    }
    
    return render_template('passport.html', citizen=citizen, passport=passport_data)


@app.route('/driving-license', methods=['GET', 'POST'])
@login_required
def driving_license():
    """Driving license renewal service (mocked)"""
    citizen = get_citizen_info()
    
    if request.method == 'POST':
        # Mock license renewal
        flash('Driving license renewal request submitted! Your new license will be mailed within 10 business days.', 'success')
        return redirect(url_for('driving_license'))
    
    # Mock license data
    license_data = {
        'number': 'DL' + citizen['id'] + '98765',
        'class': 'B',
        'issue_date': '2019-06-20',
        'expiry_date': '2029-06-19',
        'status': 'Valid',
        'points': 0
    }
    
    return render_template('driving_license.html', citizen=citizen, license=license_data)


@app.route('/building-permit', methods=['GET', 'POST'])
@login_required
def building_permit():
    """Building permit application (mocked)"""
    citizen = get_citizen_info()
    
    if request.method == 'POST':
        project_type = request.form.get('project_type', '')
        description = request.form.get('description', '')
        
        # Mock permit submission
        permit_number = 'BP' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        flash(f'Building permit application submitted! Reference number: {permit_number}. You will receive a decision within 30 days.', 'success')
        return redirect(url_for('building_permit'))
    
    # Mock existing permits
    permits = [
        {'number': 'BP20250115001', 'type': 'Extension', 'status': 'Approved', 'date': '2025-01-15'},
        {'number': 'BP20240820002', 'type': 'Renovation', 'status': 'Completed', 'date': '2024-08-20'},
    ]
    
    return render_template('building_permit.html', citizen=citizen, permits=permits)


@app.route('/trash-collection')
@login_required
def trash_collection():
    """Trash collection information (mocked)"""
    citizen = get_citizen_info()
    
    # Mock trash collection schedule based on address
    schedule = {
        'general_waste': 'Monday',
        'recycling': 'Wednesday',
        'garden_waste': 'Friday (Apr-Oct)',
        'bulk_collection': 'First Saturday of month (by appointment)'
    }
    
    # Mock upcoming collections
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
    
    return render_template('trash_collection.html', citizen=citizen, schedule=schedule, upcoming=upcoming)


@app.route('/found-dogs')
@login_required
def found_dogs():
    """Found dogs - integrates with Dogcatcher API via Kong Gateway"""
    citizen = get_citizen_info()
    dogs = []
    error = None
    
    try:
        response = requests.get(f'{API_GATEWAY_URL}/dogs/', timeout=5)
        response.raise_for_status()
        dogs = response.json()
    except requests.exceptions.ConnectionError:
        error = 'Unable to connect to the Dog Pound database. Please try again later.'
    except requests.exceptions.Timeout:
        error = 'The Dog Pound database is taking too long to respond. Please try again later.'
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving found dogs: {str(e)}'
    
    return render_template('found_dogs.html', citizen=citizen, dogs=dogs, error=error,
                          dogcatcher_url=os.environ.get('DOGCATCHER_PUBLIC_URL', 'http://localhost:5001'))


@app.route('/found-dogs/<int:dog_id>')
@login_required
def found_dog_detail(dog_id):
    """Individual dog detail page"""
    citizen = get_citizen_info()
    dog = None
    error = None
    
    try:
        response = requests.get(f'{API_GATEWAY_URL}/dogs/{dog_id}', timeout=5)
        response.raise_for_status()
        dog = response.json()
    except requests.exceptions.RequestException as e:
        error = f'Error retrieving dog details: {str(e)}'
    
    return render_template('found_dog_detail.html', citizen=citizen, dog=dog, error=error,
                          dogcatcher_url=os.environ.get('DOGCATCHER_PUBLIC_URL', 'http://localhost:5001'))


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
