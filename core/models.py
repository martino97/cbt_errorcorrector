from django.db import models
from django.contrib.auth.models import User

class CustomerError(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    )

    SEVERITY_CHOICES = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )

    identifier = models.CharField(max_length=255, blank=True)
    customer_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    national_id = models.CharField(max_length=100, blank=True)
    error_code = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    line_number = models.CharField(max_length=50, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)

    # JSON fields for additional customer data
    customer_details = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Stores additional customer details in JSON format"
    )
    customer_details_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Alternative structure for additional parsed customer info"
    )

    # File metadata
    xml_file_name = models.CharField(max_length=255, blank=True)

    # Tracking fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.error_code} - {self.customer_name} ({self.status})"

    def get_status_display(self):
        """Returns the display value for the status field."""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_severity_display(self):
        """Returns the display value for the severity field."""
        return dict(self.SEVERITY_CHOICES).get(self.severity, self.severity)
    
class SubmittedCustomerData(models.Model):
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
