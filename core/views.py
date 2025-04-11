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
import django_filters

from .models import (
    User, Department, Regulation, Article, 
    ComplianceStatus, AuditLog, Notification, 
    NotificationTemplate, SystemSetting
)
from .forms import RegulationForm, RegulationEditForm, ArticleForm, ArticleFormSet
from .elasticsearch_config import search_regulations, create_regulation_index

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

@login_required
@user_passes_test(is_compliance_user)
def compliance_regulations(request):
    regulations = Regulation.objects.all().order_by('-last_updated')
    
    # Get filter parameters
    reference = request.GET.get('reference')
    title = request.GET.get('title')
    status = request.GET.get('status')
    created_by = request.GET.get('created_by')
    department = request.GET.get('department')
    
    # Date range filters
    issue_date_from = request.GET.get('issue_date_from')
    issue_date_to = request.GET.get('issue_date_to')
    effective_date_from = request.GET.get('effective_date_from')
    effective_date_to = request.GET.get('effective_date_to')
    expiry_date_from = request.GET.get('expiry_date_from')
    expiry_date_to = request.GET.get('expiry_date_to')
    
    # Apply filters
    if reference:
        regulations = regulations.filter(reference__icontains=reference)
    if title:
        regulations = regulations.filter(name__icontains=title)
    if status:
        regulations = regulations.filter(status=status)
    if created_by:
        regulations = regulations.filter(created_by_id=created_by)
    if department:
        regulations = regulations.filter(assigned_departments__id=department)
        
    # Apply date range filters
    if issue_date_from:
        regulations = regulations.filter(issue_date__gte=issue_date_from)
    if issue_date_to:
        regulations = regulations.filter(issue_date__lte=issue_date_to)
    if effective_date_from:
        regulations = regulations.filter(effective_date__gte=effective_date_from)
    if effective_date_to:
        regulations = regulations.filter(effective_date__lte=effective_date_to)
    if expiry_date_from:
        regulations = regulations.filter(expiry_date__gte=expiry_date_from)
    if expiry_date_to:
        regulations = regulations.filter(expiry_date__lte=expiry_date_to)
    
    # Get choices for dropdowns
    status_choices = Regulation.STATUS_CHOICES
    users = User.objects.all()
    departments = Department.objects.all()
    
    context = {
        'regulations': regulations,
        'status_choices': status_choices,
        'users': users,
        'departments': departments,
        # Pass filter values back to template
        'reference_filter': reference,
        'title_filter': title,
        'status_filter': status,
        'created_by_filter': created_by,
        'department_filter': department,
        'issue_date_from': issue_date_from,
        'issue_date_to': issue_date_to,
        'effective_date_from': effective_date_from,
        'effective_date_to': effective_date_to,
        'expiry_date_from': expiry_date_from,
        'expiry_date_to': expiry_date_to,
    }
    
    return render(request, 'compliance/regulations.html', context)

@login_required
@user_passes_test(is_compliance_user)
def compliance_regulation_detail(request, regulation_id):
    """View for displaying regulation details."""
    regulation = get_object_or_404(Regulation, id=regulation_id)
    context = {
        'regulation': regulation
    }
    return render(request, 'compliance/regulation_detail.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'compliance_maker')
def create_regulation(request):
    if request.method == 'POST':
        form = RegulationForm(request.POST)
        formset = ArticleFormSet(request.POST, prefix='articles')
        
        if form.is_valid() and formset.is_valid():
            regulation = form.save(commit=False)
            regulation.created_by = request.user
            regulation.save()
            form.save_m2m()  # Save the many-to-many relationships
            
            # Save the articles if any are provided
            articles = formset.save(commit=False)
            for article in articles:
                if article.title or article.content:  # Only save if there's content
                    article.regulation = regulation
                    article.save()
            
            # Create audit log entry
            AuditLog.objects.create(
                user=request.user,
                action_type='create',
                action_details=f'Created new regulation: {regulation.name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Regulation created successfully!')
            return redirect('compliance_regulations')
        else:
            # If form is invalid, show error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for form in formset:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"Article {form.prefix}: {field}: {error}")
    else:
        form = RegulationForm()
        formset = ArticleFormSet(prefix='articles')
    
    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'compliance/create_regulation.html', context)

@login_required
@user_passes_test(is_compliance_user)
def edit_regulation(request, regulation_id):
    """View for editing existing regulations."""
    regulation = get_object_or_404(Regulation, id=regulation_id)
    
    # Check if regulation can be edited
    if regulation.status not in ['draft', 'rejected']:
        messages.error(request, 'Only draft or rejected regulations can be edited.')
        return redirect('compliance_regulation_detail', regulation_id=regulation.id)
    
    if request.method == 'POST':
        form = RegulationEditForm(request.POST, instance=regulation)
        if form.is_valid():
            regulation = form.save(commit=False)
            regulation.last_updated = timezone.now()
            regulation.save()
            form.save_m2m()  # Save the many-to-many relationships
            
            # Log the edit
            AuditLog.objects.create(
                user=request.user,
                action_type='update',
                action_details=f"Edited regulation: {regulation.name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Regulation updated successfully!')
            return redirect('compliance_regulation_detail', regulation_id=regulation.id)
    else:
        form = RegulationEditForm(instance=regulation)
    
    context = {
        'form': form,
        'regulation': regulation
    }
    return render(request, 'compliance/edit_regulation.html', context)

@login_required
@user_passes_test(lambda u: u.role == 'compliance_maker')
def delete_regulation(request, regulation_id):
    """View for deleting regulations in draft status."""
    regulation = get_object_or_404(Regulation, id=regulation_id)
    
    # Only allow deletion of draft regulations
    if regulation.status != 'draft':
        messages.error(request, 'Only draft regulations can be deleted.')
        return redirect('compliance_regulation_detail', regulation_id=regulation.id)
    
    if request.method == 'POST':
        # Create audit log entry
        AuditLog.objects.create(
            user=request.user,
            action_type='delete',
            action_details=f'Deleted regulation: {regulation.name} (Reference: {regulation.reference})',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Delete the regulation
        regulation.delete()
        messages.success(request, 'Regulation deleted successfully.')
        return redirect('compliance_regulations')
    
    return render(request, 'compliance/delete_regulation.html', {'regulation': regulation})

def regulation_list(request):
    if request.method == 'POST':
        form = RegulationForm(request.POST)
        if form.is_valid():
            regulation = form.save(commit=False)
            regulation.created_by = request.user
            regulation.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, 'Regulation created successfully.')
            return redirect('regulation_list')
    else:
        form = RegulationForm()
    
    # Get search parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    department_filter = request.GET.get('department', '')
    reference_filter = request.GET.get('reference', '')
    title_filter = request.GET.get('title', '')
    
    # Start with all regulations
    regulations = Regulation.objects.all()
    
    # Apply filters
    if status_filter:
        regulations = regulations.filter(status=status_filter)
    if department_filter:
        regulations = regulations.filter(assigned_departments__id=department_filter)
    if reference_filter:
        regulations = regulations.filter(reference__icontains=reference_filter)
    if title_filter:
        regulations = regulations.filter(name__icontains=title_filter)
    
    # Apply search if query exists
    if search_query:
        try:
            # Try Elasticsearch first
            search_results = search_regulations(search_query)
            if search_results:
                regulation_ids = [hit['_source']['id'] for hit in search_results]
                regulations = regulations.filter(id__in=regulation_ids)
            else:
                # Fallback to database search if Elasticsearch fails
                regulations = regulations.filter(
                    Q(name__icontains=search_query) |
                    Q(description__icontains=search_query) |
                    Q(reference__icontains=search_query)
                )
        except Exception as e:
            print(f"Elasticsearch error: {e}")
            # Fallback to database search
            regulations = regulations.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(reference__icontains=search_query)
            )
    
    # Get all departments for the filter dropdown
    departments = Department.objects.all()
    
    context = {
        'regulations': regulations,
        'form': form,
        'departments': departments,
        'search_query': search_query,
        'status_filter': status_filter,
        'department_filter': department_filter,
        'reference_filter': reference_filter,
        'title_filter': title_filter,
    }
    return render(request, 'compliance/regulations.html', context)

class RegulationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    reference = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.ChoiceFilter(choices=Regulation.TYPE_CHOICES)
    status = django_filters.ChoiceFilter(choices=Regulation.STATUS_CHOICES)
    created_by = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    issue_date = django_filters.DateFilter()
    effective_date = django_filters.DateFilter()
    expiry_date = django_filters.DateFilter()
    
    class Meta:
        model = Regulation
        fields = ['name', 'reference', 'type', 'status', 'created_by', 'issue_date', 'effective_date', 'expiry_date']