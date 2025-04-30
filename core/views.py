from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.http import JsonResponse
import xml.etree.ElementTree as ET
from io import BytesIO
from .models import SubmittedCustomerData, CustomerError, RecentUpload
import json

# Create this function to handle friendly error messages
def get_friendly_error_message(error_code, message=""):
    """Returns a user-friendly message based on the error code or message."""
    # You can customize this logic based on your error codes or messages
    friendly_messages = {
        'E001': 'Customer information is incomplete. Please provide all required details.',
        'E002': 'The account number format is invalid. Please check and try again.',
        'E003': 'National ID format is incorrect. Please verify and resubmit.',
        # Add more mappings as needed
    }
    
    # First try to match by error code
    if error_code in friendly_messages:
        return friendly_messages[error_code]
        
    # Default friendly message if no specific mapping exists
    return "There was an issue with the submission. Our team is working to resolve it."


@login_required
def error_dashboard(request):
    return render(request, 'dashbord.html')

def register_user(request):
    if request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not all([first_name, last_name, email, password, password2]):
            messages.error(request, 'All fields are required.')
        elif password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered.")
        elif len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
        else:
            try:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                user.save()
                messages.success(request, "Account created successfully. Please log in.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Error during registration: {e}")
    
    return render(request, 'register.html')


@login_required
def upload_both_files(request):
    if request.method == 'POST':
        customer_file = request.FILES.get('customer_file')
        error_file = request.FILES.get('error_file')
        customer_count = 0
        error_count = 0
        current_errors = []  # Track errors from this upload session

        # Clear session data about current upload
        if 'current_upload_errors' in request.session:
            del request.session['current_upload_errors']

        # === Process Customer File ===
        if customer_file:
            try:
                customer_content = customer_file.read()
                if customer_content.startswith(b'\xef\xbb\xbf'):
                    customer_content = customer_content[3:]
                root = ET.fromstring(customer_content.decode('utf-8'))
                ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}

                for command in root.findall('.//ns:Command', ns):
                    identifier = command.attrib.get('identifier', '')
                    company = command.find('.//ns:Company', ns)
                    if company is None:
                        continue

                    trade_name = company.findtext('ns:CompanyData/ns:TradeName', default='', namespaces=ns)
                    registration_number = company.findtext('ns:CompanyData/ns:RegistrationNumber', default='', namespaces=ns)
                    customer_code = company.findtext('ns:CustomerCode', default='', namespaces=ns)
                    phone = company.findtext('ns:ContactsCompany/ns:CellularPhone', default='', namespaces=ns)
                    amount = command.findtext('.//ns:TotalLoanAmount', default='0', namespaces=ns)

                    SubmittedCustomerData.objects.update_or_create(
                        identifier=identifier,
                        defaults={
                            'trade_name': trade_name,
                            'registration_number': registration_number,
                            'customer_code': customer_code,
                            'phone': phone,
                            'total_loan_amount': float(amount),
                            'submitted_by': request.user,
                        }
                    )
                    customer_count += 1
            except Exception as e:
                messages.error(request, f"Failed to process customer file: {e}")

        # === Process Error File ===
        if error_file:
            try:
                error_content = error_file.read()
                if error_content.startswith(b'\xef\xbb\xbf'):
                    error_content = error_content[3:]
                root = ET.fromstring(error_content.decode('utf-8'))
                
                # Create a unique upload identifier
                upload_session_id = f"upload_{request.user.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

                for command in root.findall('.//Command'):
                    identifier = command.attrib.get('identifier', '')
                    customer_name = command.findtext('CustomerName') or ''
                    account_number = command.findtext('AccountNumber') or ''
                    amount_str = command.findtext('Amount') or '0'
                    national_id = command.findtext('NationalID') or ''
                    try:
                        amount = float(amount_str.replace(',', '.'))
                    except ValueError:
                        amount = 0

                    for ex in command.findall('Exception'):
                        error_code = ex.findtext('ErrorCode') or 'UNKNOWN'
                        message = ''
                        line_number = ''
                        customer_details = {}
                        params_element = ex.find('Parameters')
                        if params_element is not None:
                            for param in params_element.findall('parameter'):
                                key = param.findtext('Key')
                                val = param.findtext('Value') or ''
                                if key:
                                    if key == 'Message':
                                        message = val
                                    elif key == 'LineNumber':
                                        line_number = val
                                    customer_details[key] = val

                        severity = 'medium'
                        if error_code.startswith('E'):
                            severity = 'high'
                        elif error_code.startswith('W'):
                            severity = 'low'
                        elif error_code.startswith('C'):
                            severity = 'critical'

                        # Generate friendly error message using our function
                        friendly_message = get_friendly_error_message(error_code, message)

                        # Check if this error already exists for this identifier
                        existing_error = CustomerError.objects.filter(
                            identifier=identifier, 
                            error_code=error_code,
                            message=message,
                            status='pending'  # Only check pending errors to allow resolved ones to be recreated
                        ).first()

                        if not existing_error:
                            # Create error without fields that don't exist in the database
                            error = CustomerError.objects.create(
                                identifier=identifier,
                                customer_name=customer_name,
                                account_number=account_number,
                                amount=amount,
                                national_id=national_id,
                                error_code=error_code,
                                message=message,
                                line_number=line_number,
                                severity=severity,
                                status='pending',
                                uploaded_by=request.user,
                                xml_file_name=error_file.name,
                                customer_details=customer_details
                            )
                            # Store friendly message in customer_details_json
                            error.customer_details_json = {'friendly_message': friendly_message}
                            error.save()
                            
                            error_count += 1
                            current_errors.append(error.id)
                
                # Store current upload session errors in session
                request.session['current_upload_errors'] = current_errors
                  # Store the recent upload information in session
                request.session['recent_upload'] = {
                    'timestamp': timezone.now().isoformat(),
                    'error_count': error_count,
                    'customer_count': customer_count,
                    'error_ids': current_errors,
                    'filename': error_file.name}
                
            except Exception as e:
                messages.error(request, f"Failed to process error file: {e}")
               
        # Deactivate previous recent upload for this user
        RecentUpload.objects.filter(user=request.user, is_active=True).update(is_active=False)

        # Create new recent upload record
        RecentUpload.objects.create(
            user=request.user,
            filename=error_file.name,
            customer_count=customer_count,
            error_count=error_count,
            error_ids=current_errors,
            is_active=True
        )

        messages.success(request, f"Upload completed. {customer_count} customer records and {error_count} errors saved.")
        return redirect('customer_error_dashboard')

    return render(request, 'upload_combined.html')

#display documentation in the format of pdf documents
@login_required
def documentation_view(request):
    """
    View for displaying the documentation page with regex explanations
    """
    # Structure the documentation data from the PDF
    documentation_data = [
        {
            "field_name": "Customer Code",
            "rules": "Each data provider has to provide each customer with unique code. This code is lifetime code (permanent).",
            "regex_explanation": "No specific format required, must be unique per customer."  # Added explanation
        },
        {
            "field_name": "Driving License Number",
            "rules": "Driving license for Mainland has 10 digits. Regular expression: [0-9]{10}. Driving license for Zanzibar has 9 digits. Regular expression:[Z]{1}[0-9]{9}",
            "regex_explanation": "For mainland: Exactly 10 digits (0-9). For Zanzibar: Starts with letter 'Z' followed by 9 digits."
        },
        {
            "field_name": "National ID Number",
            "rules": "National ID number has 20 digits where last digit is checksum, format is YYYYMMDD-00000-00000-1/2/3C Regular expression: [0-9]{8}(-[0-9]{5}){2}-[0-9]{2}",
            "regex_explanation": "Format: 8 digits (birth date) + hyphen + 5 digits (postal code) + hyphen + 5 digits (serial number) + hyphen + 2 digits (gender code + checksum)"
        },
        {
            "field_name": "Passport Number",
            "rules": "Format of Tanzanian passport numbers is 2 letters followed by 6 digits Regular expression: [a-zA-Z]{2}[0-9]{6}",
            "regex_explanation": "Two letters (either uppercase or lowercase) followed by exactly 6 digits"
        },
        {
            "field_name": "Voter Registration Number",
            "rules": "Voter registration number for Tanzania mainland has 8 digits Regular expression: [0-9]{8}. Voter registration number for Zanzibar has 9 digits Regular expression: [0-9]{9}",
            "regex_explanation": "For mainland: Exactly 8 digits (0-9). For Zanzibar: Exactly 9 digits (0-9)."
        },
        {
            "field_name": "Zanzibar ID",
            "rules": "Zanzibar ID number has 9 digits Regular expression: [0-9]{9}",
            "regex_explanation": "Exactly 9 digits (0-9)"
        },
        {
            "field_name": "BOT Licence Number",
            "rules": "The licence has 5 digits and 3 letters with hyphen between 1st number and 2nd number. Regular expression: [M]{1}[S]{1}[P]{1}[0-9]{5}. Example MSP2-0885",
            "regex_explanation": "Starts with 'MSP' followed by 5 digits. Note: The example seems different from the regex pattern."
        },
        {
            "field_name": "Tax Identification Number",
            "rules": "Tax identification number has 9 digits, format is xxx-xxx-xxx Regular expression: [0-9]{3}(-[0-9]{3}){2}",
            "regex_explanation": "3 digits + hyphen + 3 digits + hyphen + 3 digits (e.g., 123-456-789)"
        },
        {
            "field_name": "Cellular Phone Number",
            "rules": "International format: +255 and 9 digits (for example: +255123456789) or local format starting with '0' and 9 digits (for example: 0123456789) Regular expression: ((\\+255[0-9]{9})|(0[0-9]{9})){1}",
            "regex_explanation": "Either international format (+255 followed by 9 digits) or local format (starts with 0 followed by 9 digits)"
        },
        {
            "field_name": "Fixed Line Number",
            "rules": "International format: +255 and 9 digits (for example: +255123456789) or local format - at least 7 digits (for example: 12345678). Regular expression: ((\\+255[0-9]{9})|([0-9]{7,9})){1}",
            "regex_explanation": "Either international format (+255 followed by 9 digits) or local format (7 to 9 digits)"
        },
        {
            "field_name": "Email Address",
            "rules": "Regular expression: [A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,6}",
            "regex_explanation": "Standard email format: username@gmail.com"
        },
        {
            "field_name": "Web Page",
            "rules": "Regular expression: (http|https)\\://[a-zA-Z0-9\\-\\.]+\\.[a-zA-Z]{2,3}(:[a-zA-Z0-9]*)?/?([a-zA-Z0-9\\-\\._\\?\\,\\'\\/\\\\+&amp;%\\$#\\=~])*",
            "regex_explanation": "Standard URL format starting with http:// or https://"
        },
        {
            "field_name": "Postal Code",
            "rules": "Business Rule: Postal Code number has 5 digits Regular expression:[0-9]{5} Example: 11884",
            "regex_explanation": "Exactly 5 digits (0-9)"
        },
        # Additional fields from the PDF
        {
            "field_name": "First Name",
            "rules": "Any language",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Middle Names",
            "rules": "Any language, can contain more names",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Last Name",
            "rules": "Any language",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Birth Surname",
            "rules": "Business rule: Mandatory for all females (Gender = Female). Otherwise optional.",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Ward ID Number",
            "rules": "Number of identification document",
            "regex_explanation": "No specific format mentioned"
        },
        {
            "field_name": "Permission Number",
            "rules": "Number of identification document",
            "regex_explanation": "No specific format mentioned"
        },
        {
            "field_name": "Date of Birth",
            "rules": "Business rule: Individual must be between 18 and 99 years old!",
            "regex_explanation": "Standard date format"
        },
        {
            "field_name": "Establishment Date",
            "rules": "Business rule: Establishment date must be less than reporting date.",
            "regex_explanation": "Standard date format"
        },
        {
            "field_name": "Date of Issuance",
            "rules": "Business rule: Issuance date must not be greater than reporting date.",
            "regex_explanation": "Standard date format"
        },
        {
            "field_name": "Date of Expiration",
            "rules": "Business rule: Expiration date must not be less than issuance date. Business rule: Expiration date must not be less than reporting date.",
            "regex_explanation": "Standard date format"
        },
        {
            "field_name": "BRELA and BPRA Registration Number",
            "rules": "Registration number has from 1 to 6 digits Regular expression: [0-9]{1,6} Example: 123456. For Zanzibar registration number has 1 letter and 10 digits. Regular expression: [Z]{1}[0-9]{10}. Example: Z0000019264",
            "regex_explanation": "For mainland: 1 to 6 digits. For Zanzibar: Letter 'Z' followed by 10 digits"
        },
        {
            "field_name": "Registration Number (Entrepreneur)",
            "rules": "Includes registration number from recognized authorities: BRELA, BPRA, TCDC and Other Government Agencies.",
            "regex_explanation": "Format depends on issuing authority"
        },
        {
            "field_name": "Business Name",
            "rules": "Name of business",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "License Number",
            "rules": "Business licence number",
            "regex_explanation": "No specific format mentioned"
        },
        {
            "field_name": "Trade Name",
            "rules": "Any language.",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Employer Name",
            "rules": "Name of employer - to be used only if employer cannot be identified fully in section RELATION",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Monthly Income",
            "rules": "Combination of two fields (Decimal1804 for amount value and Lookup for currency). Business rule: Amount can not be negative",
            "regex_explanation": "Numeric value with currency code"
        },
        {
            "field_name": "Monthly Expenditures",
            "rules": "Combination of two fields (Decimal1804 for amount value and Lookup for currency). Business rule: Amount can not be negative",
            "regex_explanation": "Numeric value with currency code"
        },
        {
            "field_name": "Number of Dependants - Children",
            "rules": "Nr. of children",
            "regex_explanation": "Integer value"
        },
        {
            "field_name": "Number of Dependants - Spouses",
            "rules": "Nr. of spouses",
            "regex_explanation": "Integer value"
        },
        {
            "field_name": "Number of Employees",
            "rules": "Number of employees",
            "regex_explanation": "Integer value"
        },
        {
            "field_name": "Spouse Full Name",
            "rules": "Field can be repeated for each husband or wife name. Field should contain full name (including the middle names)",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Location of Issuance",
            "rules": "The location where the ID was issued.",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Issued By",
            "rules": "The name or organization which issued the document.",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Full Name of Person",
            "rules": "Full name of contact person",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "City - Town - Village",
            "rules": "Location name",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Country",
            "rules": "See sheet \"Country codes\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "District",
            "rules": "See sheet \"District\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Region",
            "rules": "See sheet \"Region\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Street / Ward",
            "rules": "Street or ward name",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "House Number",
            "rules": "House number identifier",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "P.O.BOX Number",
            "rules": "Post office box number",
            "regex_explanation": "No specific format required"
        },
        {
            "field_name": "Fax Number",
            "rules": "International format: +255 and 9 digits (for example: +255123456789) or local format - at least 7 digits (for example: 12345678). Regular expression: ((\\+255[0-9]{9})|([0-9]{7,9})){1}",
            "regex_explanation": "Either international format (+255 followed by 9 digits) or local format (7 to 9 digits)"
        },
        {
            "field_name": "Individual Classification",
            "rules": "See attribute table D01 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Negative Status of Client",
            "rules": "See attribute table D04 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Marital Status",
            "rules": "See attribute table D17 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Gender",
            "rules": "See attribute table D03 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Nationality",
            "rules": "See sheet \"Country codes\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Citizenship",
            "rules": "See sheet \"Country codes\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Profession",
            "rules": "See sheet \"Profession\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Education (Highest Achieved)",
            "rules": "See attribute table D20 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "District of Birth",
            "rules": "See sheet \"District\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Legal Form",
            "rules": "See attribute table D05 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Registration Country",
            "rules": "See sheet \"Country Codes\" for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Relation Type",
            "rules": "See attribute table D22 for lookup values",
            "regex_explanation": "Value from lookup table"
        },
        {
            "field_name": "Value of Shares Owned (in %)",
            "rules": "Business rule: Amount can not be negative",
            "regex_explanation": "Decimal percentage value"
        },
        {
            "field_name": "Value of Shares Owned (Amount)",
            "rules": "See sheet \"Currencies\" for lookup values Business rule: Amount can not be negative",
            "regex_explanation": "Numeric value with currency code"
        },
        {
            "field_name": "Additional Information",
            "rules": "Free text up to 255 chars.",
            "regex_explanation": "Free text with maximum 255 characters"
        }
    ]
    
    context = {
        'documentation_data': documentation_data,
        'title': 'Documentation',
    }
    
    return render(request, 'documentation.html', context)
@login_required
def customer_error_dashboard(request):
    # Handle the status update
    if request.method == 'POST' and 'error_id' in request.POST and 'status' in request.POST:
        error_id = request.POST.get('error_id')
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        try:
            error = CustomerError.objects.get(id=error_id)
            if new_status in ['pending', 'resolved', 'ignored']:
                error.status = new_status
                error.notes = notes
                if new_status == 'resolved' and error.status != 'resolved':
                    error.resolved_by = request.user
                    error.resolved_at = timezone.now()
                error.save()
                messages.success(request, f"Error status updated to {error.get_status_display()}.")
                
                # For AJAX requests
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
        except CustomerError.DoesNotExist:
            messages.error(request, "Error not found.")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Error not found'})
        except Exception as e:
            messages.error(request, f"Error updating status: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
    
    # Determine which status to show
    status_filter = request.GET.get('status', 'pending')
    
    # Get all errors for counting purposes
    all_errors = CustomerError.objects.select_related('uploaded_by').all()
    
    # Filter errors based on status
    if status_filter == 'all':
        errors = all_errors
    else:
        errors = all_errors.filter(status=status_filter)
    
    # Get counts for display
    total_errors = all_errors.count()
    pending_errors = all_errors.filter(status='pending').count()
    resolved_errors = all_errors.filter(status='resolved').count()
    ignored_errors = all_errors.filter(status='ignored').count()
    
    # Check if we have current upload session errors
    current_upload_errors = request.session.get('current_upload_errors', [])
    current_upload_count = len(current_upload_errors) if current_upload_errors else 0
    
    # Group errors by identifiers to avoid duplicates
    unique_errors = {}
    for error in errors:
        # Only include the first occurrence of each error code for an identifier
        key = f"{error.identifier}_{error.error_code}"
        if key not in unique_errors:
            submitted = SubmittedCustomerData.objects.filter(identifier=error.identifier).first()
            
            # Use the error translator utility to get the friendly message
            from .error_translator_utils import process_dashboard_error
            friendly_message = process_dashboard_error(error.error_code, error.message)
            
            # Store the friendly message directly on the error object
            error.friendly_message = friendly_message
                
            unique_errors[key] = {
                'error': error,
                'submitted': submitted
            }
    
    # Convert to list for template
    data = list(unique_errors.values())
    
    # Get most recent upload for current user
    recent_upload = RecentUpload.objects.filter(user=request.user, is_active=True).first()
    
    recent_errors = []
    if recent_upload:
        recent_errors_raw = CustomerError.objects.filter(id__in=recent_upload.error_ids)
        for error in recent_errors_raw:
            # Get corresponding submitted data
            submitted = SubmittedCustomerData.objects.filter(identifier=error.identifier).first()
            
            # Get friendly message
            from .error_translator_utils import process_dashboard_error
            friendly_message = process_dashboard_error(error.error_code, error.message)
            
            error_data = {
                'error': error,
                'submitted': submitted,
                'friendly_message': friendly_message
            }
            recent_errors.append(error_data)

    context = {
        'data': data,
        'error_stats': {
            'total': total_errors,
            'pending': pending_errors,
            'resolved': resolved_errors
        },
        'current_upload': {
            'timestamp': recent_upload.timestamp if recent_upload else None,
            'customer_count': recent_upload.customer_count if recent_upload else 0,
            'error_count': recent_upload.error_count if recent_upload else 0,
            'filename': recent_upload.filename if recent_upload else '',
            'recent_errors': recent_errors
        },
        'status_filter': status_filter
    }
    
    return render(request, 'error_dashboard.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('customer_error_dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('customer_error_dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})