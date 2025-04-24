from django.contrib import admin
from .models import CustomerError

@admin.register(CustomerError)
class CustomerErrorAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'customer_name', 'error_code', 'severity', 'status', 'created_at')
    list_filter = ('severity', 'status', 'created_at')
    search_fields = ('customer_name', 'account_number', 'error_code', 'national_id')
    date_hierarchy = 'created_at'