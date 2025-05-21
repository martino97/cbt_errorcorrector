from django.contrib import admin
from .models import CustomerError, RecentUpload, CleanEntry, ErrorHistory,BatchHistory

@admin.register(CustomerError)
class CustomerErrorAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'customer_name', 'error_code', 'severity', 'status', 'created_at')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('customer_name', 'account_number', 'error_code', 'national_id')
    date_hierarchy = 'created_at'

@admin.register(RecentUpload)
class RecentUploadAdmin(admin.ModelAdmin):
    list_display = ('filename', 'user', 'timestamp', 'customer_count', 'error_count', 'is_active')
    list_filter = ('is_active', 'timestamp')
    search_fields = ('filename', 'user__username')
    date_hierarchy = 'timestamp'
    # Optional: Display user-friendly username in list_display
    def user(self, obj):
        return obj.user.username
    user.admin_order_field = 'user__username'  # Enable sorting by username

@admin.register(CleanEntry)
class CleanEntryAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'customer_name', 'account_number', 'amount', 'batch_identifier', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('identifier', 'customer_name', 'account_number', 'national_id', 'customer_code', 'batch_identifier')
    date_hierarchy = 'created_at'

@admin.register(ErrorHistory)
class ErrorHistoryAdmin(admin.ModelAdmin):
    list_display = ('error_identifier', 'previous_status', 'new_status', 'changed_at', 'changed_by')
    list_filter = ('previous_status', 'new_status', 'changed_at')
    search_fields = ('error__identifier', 'notes', 'changed_by__username')
    date_hierarchy = 'changed_at'
    # Optional: Display error identifier in list_display
    def error_identifier(self, obj):
        return obj.error.identifier
    error_identifier.admin_order_field = 'error__identifier'  # Enable sorting by error identifier
    # Optional: Display username of changed_by
    def changed_by(self, obj):
        return obj.changed_by.username if obj.changed_by else 'N/A'
    changed_by.admin_order_field = 'changed_by__username'  # Enable sorting by username

@admin.register(BatchHistory)
class BatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('batch_identifier', 'uploaded_by', 'upload_date', 'status', 'error_count', 'filename')
    list_filter = ('status', 'upload_date')
    search_fields = ('batch_identifier', 'filename', 'uploaded_by__username')
    date_hierarchy = 'upload_date'
    def uploaded_by(self, obj):
        return obj.uploaded_by.username
    uploaded_by.admin_order_field = 'uploaded_by__username'