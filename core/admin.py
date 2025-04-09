from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html
from .models import (
    User, Department, Regulation, Article, 
    ComplianceStatus, AuditLog, Notification, 
    NotificationTemplate, SystemSetting
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'display_departments')
    list_filter = ('role', 'is_active', 'departments')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role')}),
        ('Departments', {'fields': ('departments',)}),
    )
    filter_horizontal = ('departments', 'user_permissions', 'groups')
    
    def display_departments(self, obj):
        return ", ".join([dept.name for dept in obj.departments.all()])
    display_departments.short_description = 'Departments'

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at', 'user_count')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    
    def user_count(self, obj):
        return obj.users.count()
    user_count.short_description = 'Number of Users'

class ArticleInline(admin.TabularInline):
    model = Article
    extra = 1
    fields = ('title', 'content', 'order')

class RegulationAdmin(ImportExportModelAdmin):
    list_display = ('name', 'status', 'date_created', 'last_updated', 'created_by', 'department_count')
    list_filter = ('status', 'date_created', 'assigned_departments')
    search_fields = ('name', 'description')
    filter_horizontal = ('assigned_departments',)
    inlines = [ArticleInline]
    
    def department_count(self, obj):
        return obj.assigned_departments.count()
    department_count.short_description = 'Assigned Departments'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'regulation', 'order', 'date_created', 'last_updated')
    list_filter = ('regulation', 'date_created')
    search_fields = ('title', 'content', 'regulation__name')

class ComplianceStatusAdmin(admin.ModelAdmin):
    list_display = ('article', 'department', 'status', 'created_by', 'created_at', 'updated_at')
    list_filter = ('status', 'department', 'created_at')
    search_fields = ('article__title', 'department__name', 'comments')
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'action_details', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp', 'user')
    search_fields = ('user__username', 'action_details', 'ip_address')
    readonly_fields = ('user', 'action_type', 'action_details', 'timestamp', 'ip_address')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'read', 'created_at', 'related_regulation')
    list_filter = ('read', 'created_at', 'recipient')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at',)

class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'subject', 'active')
    list_filter = ('active', 'event_type')
    search_fields = ('name', 'subject', 'body')

class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('setting_key', 'value', 'updated_at')
    search_fields = ('setting_key', 'value', 'description')
    readonly_fields = ('created_at', 'updated_at')

# Register all models with their custom admin classes
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department, DepartmentAdmin)
admin.site.register(Regulation, RegulationAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(ComplianceStatus, ComplianceStatusAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(SystemSetting, SystemSettingAdmin)
