from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('compliance_maker', 'Compliance Maker'),
        ('compliance_checker', 'Compliance Checker'),
        ('dept_maker', 'Department Maker'),
        ('dept_checker', 'Department Checker'),
    ]
    
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='dept_maker')
    departments = models.ManyToManyField(Department, related_name='users', blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class Regulation(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_regulations')
    assigned_departments = models.ManyToManyField(Department, related_name='assigned_regulations')
    
    def __str__(self):
        return self.name

class Article(models.Model):
    regulation = models.ForeignKey(Regulation, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.regulation.name} - {self.title}"

class ComplianceStatus(models.Model):
    STATUS_CHOICES = [
        ('compliant', 'Compliant'),
        ('partially_compliant', 'Partially Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('not_applicable', 'Not Applicable'),
    ]
    
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='compliance_statuses')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    comments = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_statuses')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_statuses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['article', 'department']
        verbose_name_plural = 'Compliance statuses'
    
    def __str__(self):
        return f"{self.article} - {self.department} - {self.status}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('status_change', 'Status Change'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    action_details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.timestamp}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_regulation = models.ForeignKey(Regulation, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.recipient} - {self.title} - {self.created_at}"

class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    event_type = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class SystemSetting(models.Model):
    COMPLIANCE_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannually', 'Biannually'),
        ('annually', 'Annually'),
    ]
    
    setting_key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.setting_key
