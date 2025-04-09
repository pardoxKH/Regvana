from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import AuditLog
import json

class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log user actions for auditing purposes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.async_mode = False
        # Exclude these URLs from logging
        self.excluded_urls = [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/get_notifications/',
        ]
        # Exclude these extensions from logging
        self.excluded_extensions = ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']
    
    def _should_log(self, request):
        # Don't log excluded URLs
        for url in self.excluded_urls:
            if request.path.startswith(url):
                return False
        
        # Don't log static files
        for ext in self.excluded_extensions:
            if request.path.endswith(ext):
                return False
        
        # Only log certain methods
        if request.method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            return False
        
        return True
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not self._should_log(request) or not request.user.is_authenticated:
            return None
        
        # Get URL name
        url_name = resolve(request.path_info).url_name
        
        # Determine action type based on request method and URL
        if 'login' in url_name:
            action_type = 'login'
        elif 'logout' in url_name:
            action_type = 'logout'
        elif request.method == 'POST' and ('add' in url_name or 'create' in url_name):
            action_type = 'create'
        elif request.method == 'POST' and ('change' in url_name or 'edit' in url_name or 'update' in url_name):
            action_type = 'update'
        elif request.method == 'POST' and ('delete' in url_name or 'remove' in url_name):
            action_type = 'delete'
        elif 'status' in url_name or 'approve' in url_name or 'reject' in url_name:
            action_type = 'status_change'
        else:
            action_type = request.method.lower()
        
        # Collect details for the log
        action_details = {
            'url': request.path,
            'method': request.method,
            'url_name': url_name,
        }
        
        # Add request parameters (safely)
        if request.method == 'GET':
            action_details['params'] = dict(request.GET.items())
        elif request.method == 'POST':
            # Only log POST data for non-sensitive forms
            if 'password' not in request.POST and 'csrfmiddlewaretoken' not in request.POST:
                action_details['data'] = dict(request.POST.items())
        
        # Create the audit log entry
        AuditLog.objects.create(
            user=request.user,
            action_type=action_type,
            action_details=json.dumps(action_details),
            ip_address=self.get_client_ip(request)
        )
        
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 