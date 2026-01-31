"""
Custom decorators for the citizen app.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_required(f):
    """Decorator to require citizen login for views."""
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        if 'citizen_id' not in request.session:
            messages.warning(request, 'Please log in to access this service.')
            return redirect('login')
        return f(request, *args, **kwargs)
    return decorated_function
