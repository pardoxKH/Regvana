from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import csv
import json
from datetime import datetime, timedelta

from .models import (
    User, Department, Regulation, Article, 
    ComplianceStatus, AuditLog, Notification, 
    NotificationTemplate, SystemSetting
)

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role == 'admin')

def is_compliance_user(user):
    return user.is_authenticated and user.role in ['compliance_maker', 'compliance_checker']

# Admin Views
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get counts for various models
    user_count = User.objects.count()
    department_count = Department.objects.count()
    regulation_count = Regulation.objects.count()
    article_count = Article.objects.count()
    
    # Get regulations by status
    regulation_by_status = Regulation.objects.values('status').annotate(count=Count('id'))
    
    # Get recent audit logs
    recent_logs = AuditLog.objects.order_by('-timestamp')[:10]
    
    # Get recent notifications
    recent_notifications = Notification.objects.order_by('-created_at')[:5]
    
    # Get departments with compliance status counts
    departments_compliance = []
    for dept in Department.objects.all():
        compliant = ComplianceStatus.objects.filter(department=dept, status='compliant').count()
        partially = ComplianceStatus.objects.filter(department=dept, status='partially_compliant').count()
        non_compliant = ComplianceStatus.objects.filter(department=dept, status='non_compliant').count()
        
        departments_compliance.append({
            'department': dept,
            'compliant': compliant,
            'partially_compliant': partially,
            'non_compliant': non_compliant,
            'total': compliant + partially + non_compliant
        })
    
    context = {
        'user_count': user_count,
        'department_count': department_count,
        'regulation_count': regulation_count,
        'article_count': article_count,
        'regulation_by_status': regulation_by_status,
        'recent_logs': recent_logs,
        'recent_notifications': recent_notifications,
        'departments_compliance': departments_compliance,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def export_audit_logs(request):
    # Get date range from request
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    user_id = request.GET.get('user_id')
    action_type = request.GET.get('action_type')
    
    # Start with all logs
    logs = AuditLog.objects.all()
    
    # Apply filters
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            # Add one day to include end_date in range
            end_date = end_date + timedelta(days=1)
            logs = logs.filter(timestamp__range=[start_date, end_date])
        except ValueError:
            pass
    
    if user_id:
        logs = logs.filter(user_id=user_id)
    
    if action_type:
        logs = logs.filter(action_type=action_type)
    
    # Order by timestamp descending
    logs = logs.order_by('-timestamp')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Action Type', 'Action Details', 'Timestamp', 'IP Address'])
    
    for log in logs:
        writer.writerow([
            log.user.username if log.user else 'System',
            log.action_type,
            log.action_details,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.ip_address or 'N/A'
        ])
    
    return response

@login_required
@user_passes_test(is_admin)
def export_regulations(request):
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="regulations.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Description', 'Status', 'Date Created', 'Last Updated', 'Created By', 'Assigned Departments'])
    
    for reg in Regulation.objects.all():
        writer.writerow([
            reg.name,
            reg.description,
            reg.status,
            reg.date_created.strftime('%Y-%m-%d'),
            reg.last_updated.strftime('%Y-%m-%d'),
            reg.created_by.username if reg.created_by else 'N/A',
            ', '.join([dept.name for dept in reg.assigned_departments.all()])
        ])
    
    return response

# Notification related views
@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user, read=False).order_by('-created_at')
    data = []
    
    for notification in notifications:
        data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M'),
        })
    
    return JsonResponse({'notifications': data})

@login_required
@csrf_exempt
def mark_notification_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.read = True
        notification.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

# Compliance Portal Views
def login_redirect_view(request):
    """Redirect users based on their role after login."""
    # If user is not authenticated, show login page
    if not request.user.is_authenticated:
        return redirect('login')
        
    # Log the login event
    AuditLog.objects.create(
        user=request.user,
        action_type='login',
        action_details=f"User {request.user.username} logged in",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Redirect based on role
    if request.user.is_superuser or request.user.role == 'admin':
        return redirect('admin:index')
    elif request.user.role in ['compliance_maker', 'compliance_checker']:
        return redirect('compliance_dashboard')
    else:
        # For other roles, redirect to admin site
        return redirect('admin:index')

@login_required
@user_passes_test(is_compliance_user)
def compliance_dashboard(request):
    """Dashboard view for compliance users (makers and checkers)."""
    # Get the user's unread notifications
    unread_notifications = Notification.objects.filter(recipient=request.user, read=False).order_by('-created_at')
    
    context = {
        'unread_notifications': unread_notifications
    }
    
    # Add more role-specific data here in the future
    
    return render(request, 'compliance/dashboard.html', context)
