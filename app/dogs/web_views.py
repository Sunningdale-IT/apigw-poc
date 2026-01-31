"""
Web views for the Dogcatcher application (HTML interface).
"""
import os
import re
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Dog


def secure_filename(filename):
    """Make a filename secure by removing or replacing unsafe characters."""
    # Remove path separators
    filename = os.path.basename(filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Keep only safe characters
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '', filename)
    # Ensure it's not empty
    if not filename:
        filename = 'unnamed'
    return filename


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS


def validate_coordinates(latitude, longitude):
    """Validate GPS coordinates are within valid ranges."""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180


def index(request):
    """Home page with navigation."""
    return render(request, 'index.html')


def admin_page(request):
    """Admin page to add new dog entries."""
    return render(request, 'admin.html')


@csrf_exempt
def add_dog(request):
    """Handle form submission to add a new dog.
    
    Note: csrf_exempt is used to allow the test data loader script
    to submit forms without a CSRF token.
    """
    if request.method != 'POST':
        return redirect('admin')
    
    try:
        # Validate required fields
        name = request.POST.get('name', '').strip()
        breed = request.POST.get('breed', '').strip()
        
        if not name or not breed:
            messages.error(request, 'Name and breed are required fields.')
            return redirect('admin')
        
        # Validate and convert coordinates
        try:
            latitude = float(request.POST.get('latitude'))
            longitude = float(request.POST.get('longitude'))
        except (TypeError, ValueError):
            messages.error(request, 'Invalid GPS coordinates. Please enter valid numbers.')
            return redirect('admin')
        
        # Validate coordinate ranges
        if not validate_coordinates(latitude, longitude):
            messages.error(request, 'GPS coordinates out of valid range. Latitude must be between -90 and 90, longitude between -180 and 180.')
            return redirect('admin')
        
        comments = request.POST.get('comments', '')
        
        # Handle file upload with validation
        photo = None
        if 'photo' in request.FILES:
            uploaded_file = request.FILES['photo']
            if uploaded_file.name:
                if not allowed_file(uploaded_file.name):
                    messages.error(request, 'Invalid file type. Only PNG, JPG, JPEG, and GIF images are allowed.')
                    return redirect('admin')
                
                filename = secure_filename(uploaded_file.name)
                # Add timestamp to avoid filename collisions
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
                photo_filename = timestamp + filename
                
                # Save file
                photo_path = os.path.join(settings.MEDIA_ROOT, photo_filename)
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                with open(photo_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                photo = photo_filename
        
        # Create new dog entry
        new_dog = Dog(
            name=name,
            latitude=latitude,
            longitude=longitude,
            breed=breed,
            comments=comments
        )
        if photo:
            new_dog.photo_filename = photo
        new_dog.save()
        
        messages.success(request, f'Successfully added {name} to the database!')
        return redirect('admin')
        
    except Exception as e:
        messages.error(request, f'Error adding dog: {str(e)}')
        return redirect('admin')


def browse(request):
    """Browse all dogs in the database."""
    dogs = Dog.objects.all().order_by('-caught_date')
    return render(request, 'browse.html', {'dogs': dogs})


def delete_dog(request, dog_id):
    """Delete a dog from the database."""
    if request.method != 'POST':
        return redirect('browse')
    
    try:
        dog = get_object_or_404(Dog, id=dog_id)
        dog_name = dog.name
        
        # Delete photo file if it exists
        if dog.photo_filename:
            photo_path = os.path.join(settings.MEDIA_ROOT, dog.photo_filename)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except OSError as e:
                    print(f"Warning: Could not delete photo file: {e}")
        
        dog.delete()
        
        messages.success(request, f'Successfully deleted {dog_name} from the database.')
    except Exception as e:
        messages.error(request, f'Error deleting dog: {str(e)}')
    
    return redirect('browse')
