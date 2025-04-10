"""
URL configuration for compliance_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

# Customize admin site
admin.site.site_header = 'Compliance Platform Administration'
admin.site.site_title = 'Compliance Platform Admin'
admin.site.index_title = 'Welcome to Compliance Platform'

# This function is no longer needed as we're using the login_redirect_view
# def redirect_to_admin(request):
#     return redirect('admin:index')

urlpatterns = [
    # Authentication URLs - must come before other routes
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Admin URLs
    path('admin/', admin.site.urls),
    path('admin/dashboard/', core_views.admin_dashboard, name='admin_dashboard'),
    path('admin/export/audit-logs/', core_views.export_audit_logs, name='export_audit_logs'),
    path('admin/export/regulations/', core_views.export_regulations, name='export_regulations'),
    
    # Compliance portal
    path('compliance/', core_views.compliance_dashboard, name='compliance_dashboard'),
    
    # Notification endpoints
    path('get_notifications/', core_views.get_notifications, name='get_notifications'),
    path('mark_notification_read/<int:notification_id>/', core_views.mark_notification_read, name='mark_notification_read'),
    
    # Root URL - redirect based on role
    path('', core_views.login_redirect_view, name='home'),
]
