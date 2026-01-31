"""
Custom permissions for the Dogcatcher API.
"""
from rest_framework import permissions
from django.conf import settings


class APIKeyPermission(permissions.BasePermission):
    """
    Custom permission to require API key authentication.
    
    Supports multiple authentication modes:
    - X-API-Key header: Standard API key authentication
    - X-Auth-Verified header: Pre-authenticated requests from API gateway (Kong/nginx)
    - API_KEY_REQUIRED=false: Disable all authentication
    """
    message = 'API key is required. Please provide X-API-Key header.'
    
    def has_permission(self, request, view):
        # Check if API key enforcement is disabled globally
        if not settings.API_KEY_REQUIRED:
            return True
        
        # Check if request is pre-authenticated by API gateway
        # Kong or nginx can set this header after verifying auth
        auth_verified = request.headers.get('X-Auth-Verified', '').lower()
        if auth_verified == 'true':
            return True
        
        # Check for public route indicator (set by Kong for public routes)
        auth_mode = request.headers.get('X-Auth-Mode', '').lower()
        if auth_mode == 'public':
            return True
        
        # Check if any API keys are configured
        if not settings.API_KEYS:
            self.message = 'API key authentication is enabled but no API keys are configured'
            return False
        
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            self.message = 'API key is required. Please provide X-API-Key header.'
            return False
        
        if api_key not in settings.API_KEYS:
            self.message = 'Invalid API key'
            return False
        
        return True


class AllowAny(permissions.BasePermission):
    """
    Allow any access - used for public endpoints.
    """
    def has_permission(self, request, view):
        return True
