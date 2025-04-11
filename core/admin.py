from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Department, Regulation, Article, 
    ComplianceStatus, AuditLog, Notification, 
    NotificationTemplate, SystemSetting
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Role and Departments'), {'fields': ('role', 'departments')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    filter_horizontal = ('groups', 'user_permissions', 'departments')
    
    # Add role-specific actions
    actions = ['make_compliance_maker', 'make_compliance_checker']
    
    def make_compliance_maker(self, request, queryset):
        queryset.update(role='compliance_maker')
    make_compliance_maker.short_description = "Set selected users as Compliance Makers"
    
    def make_compliance_checker(self, request, queryset):
        queryset.update(role='compliance_checker')
    make_compliance_checker.short_description = "Set selected users as Compliance Checkers"

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')

class ArticleInline(admin.TabularInline):
    model = Article
    extra = 1

class RegulationAdmin(ImportExportModelAdmin):
    list_display = ('name', 'status', 'created_by', 'date_created', 'last_updated')
    list_filter = ('status', 'date_created')
    search_fields = ('name', 'description')
    readonly_fields = ('date_created', 'last_updated')
    inlines = [ArticleInline]
    filter_horizontal = ('assigned_departments',)

class ComplianceStatusAdmin(admin.ModelAdmin):
    list_display = ('article', 'department', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('article__title', 'department__name', 'comments')
    readonly_fields = ('created_at', 'updated_at')

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__username', 'action_details')
    readonly_fields = ('user', 'action_type', 'action_details', 'timestamp', 'ip_address')
    
    # Disable add/edit/delete functionality
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'read', 'created_at')
    list_filter = ('read', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')

class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'active')
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
admin.site.register(ComplianceStatus, ComplianceStatusAdmin)
admin.site.register(AuditLog, AuditLogAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(SystemSetting, SystemSettingAdmin)
