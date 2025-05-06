from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

import json

class BatchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    batch_identifier = models.CharField(max_length=100, unique=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    resolved_date = models.DateTimeField(null=True, blank=True)
    error_count = models.IntegerField(default=0)
    xml_file = models.FileField(upload_to='xml_uploads/')
    report_file = models.FileField(upload_to='bot_reports/', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('resolved', 'Resolved')
        ),
        default='pending'
    )
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='uploaded_batches'
    )
    filename = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Batch Histories"
        ordering = ['-upload_date']

    def __str__(self):
        return f"Batch {self.batch_identifier}"

class CustomerError(models.Model):
    id = models.AutoField(primary_key=True)
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('ok', 'OK'),
    )

    SEVERITY_CHOICES = (
        ('error', 'Error'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    )

    # Core fields
    batch = models.ForeignKey(BatchHistory, on_delete=models.CASCADE, related_name='errors')
    identifier = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    national_id = models.CharField(max_length=100, blank=True)
    customer_code = models.CharField(max_length=50, blank=True)
    error_code = models.CharField(max_length=50)
    message = models.TextField(blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    
    # Status fields
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='error')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    # JSON data
    customer_details = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Stores additional customer details in JSON format"
    )
    
    # File data
    xml_file_name = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # User relations
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_errors'
    )
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_errors'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.identifier} - {self.error_code}"

    def get_status_display(self):
        """Returns the display value for the status field."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_severity_display(self):
        """Returns the display value for the severity field."""
        return dict(self.SEVERITY_CHOICES).get(self.severity, self.severity)
        
    def get_customer_details_display(self):
        """Return customer details as a dictionary."""
        if not self.customer_details:
            return {}
        
        if isinstance(self.customer_details, str):
            try:
                return json.loads(self.customer_details)
            except json.JSONDecodeError:
                return {'error': 'Invalid JSON format'}
        return self.customer_details
    
class SubmittedCustomerData(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=100, unique=True)
    trade_name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100)
    customer_code = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    total_loan_amount = models.DecimalField(max_digits=20, decimal_places=4)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.identifier} - {self.trade_name}"

class RecentUpload(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    customer_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    error_ids = models.JSONField(default=list)  # Changed from models.JSONField() to models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.filename} - {self.timestamp}"

class CleanEntry(models.Model):
    id = models.AutoField(primary_key=True)
    identifier = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    national_id = models.CharField(max_length=100)
    customer_code = models.CharField(max_length=100)
    batch_identifier = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='ok')
    created_at = models.DateTimeField(auto_now_add=True)
    xml_file_name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Clean Entries"
        ordering = ['-created_at']

class ErrorHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL
    )
    error = models.ForeignKey(
        'CustomerError',
        on_delete=models.CASCADE,
        related_name='history'
    )

    class Meta:
        verbose_name_plural = "Error Histories"
        ordering = ['-changed_at']

    def __str__(self):
        return f"Error {self.error.identifier} status change: {self.previous_status} -> {self.new_status}"