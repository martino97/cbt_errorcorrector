from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import xml.etree.ElementTree as ET
from io import BytesIO
from .models import SubmittedCustomerData, CustomerError, RecentUpload
import json
from core import BOTXMLValidator
from django.core.files.storage import FileSystemStorage
import os
from .validation_config import validation_dict, validation_dict_by_code, validate_xml_file
from .models import BatchHistory
import csv
from datetime import datetime
from django.db import transaction
from django.db.models import Q  # Add this import
from django.conf import settings  # Add this import

# Create this function to handle friendly error messages
def get_friendly_error_message(error_code, message=""):
    """Returns a user-friendly message based on the error code or message."""
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

# Add this helper function at the top of the file
def get_batch_identifier(xml_content, is_customer_file=False):
    """Extract batch identifier from XML Header block"""
    try:
        root = ET.fromstring(xml_content.decode('utf-8'))
        if is_customer_file:
            ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}
            batch_id = root.find('.//ns:Header/ns:Identifier', ns)
        else:
            batch_id = root.find('.//Header/Identifier')
            
        if batch_id is None:
            return None
        return batch_id.text.strip()
    except ET.ParseError:
        return None


@login_required
def error_dashboard(request):
    # Get batch filter if present
    batch_id = request.GET.get('batch')
    
    # Get errors with related batch and customer data
    errors = CustomerError.objects.select_related('batch').all()
    
    if batch_id:
        errors = errors.filter(batch__batch_identifier=batch_id)
    
    # Get customer data for each error
    for error in errors:
        # Get customer data from SubmittedCustomerData
        customer_data = SubmittedCustomerData.objects.filter(
            identifier=error.identifier
        ).first()
        
        if customer_data:
            error.customer_name = customer_data.birth_surname
            error.customer_code = customer_data.customer_code
            error.phone = customer_data.phone
            error.loan_amount = customer_data.total_loan_amount
        else:
            error.customer_name = error.customer_details.get('birth_surname', '')
            error.customer_code = error.customer_details.get('customer_code', '')
            error.phone = error.customer_details.get('phone', '')
            error.loan_amount = error.customer_details.get('loan_amount', '0.00')
    
    context = {
        'errors': errors,
        'batch_id': batch_id
    }
    
    return render(request, 'error_dashboard.html', context)

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
        customer_batch_id = None  # Initialize variable here

        # Clear session data about current upload
        if 'current_upload_errors' in request.session:
            del request.session['current_upload_errors']

        # === Check Batch Identifiers ===
        if customer_file and error_file:
            try:
                # Read customer file content
                customer_content = customer_file.read()
                if customer_content.startswith(b'\xef\xbb\xbf'):
                    customer_content = customer_content[3:]
                    
                # Read error file content
                error_content = error_file.read()
                if error_content.startswith(b'\xef\xbb\xbf'):
                    error_content = error_content[3:]

                # Get batch identifiers from Header block
                customer_batch_id = get_batch_identifier(customer_content, is_customer_file=True)
                error_batch_id = get_batch_identifier(error_content)

                # Check if identifiers were found in Header block
                if not customer_batch_id:
                    messages.error(request, "Could not find BatchIdentifier in customer file Header block. Example: TZ0230653")
                    return render(request, 'upload_combined.html')
                    
                if not error_batch_id:
                    messages.error(request, "Could not find BatchIdentifier in error file Header block. Example: TZ0230653")
                    return render(request, 'upload_combined.html')

                # Compare batch identifiers
                if customer_batch_id != error_batch_id:
                    messages.error(request, 
                        f"Files cannot be processed - Batch identifiers in Header do not match!\n\n"
                        f"Customer File Batch ID: {customer_batch_id}\n"
                        f"Error File Batch ID: {error_batch_id}\n\n"
                        f"Please ensure you are uploading files from the same batch (e.g., TZ0230653)."
                    )
                    return render(request, 'upload_combined.html')

                # Reset file pointers for later processing
                customer_file.seek(0)
                error_file.seek(0)

            except Exception as e:
                messages.error(request, f"Error checking batch identifiers in Header block: {str(e)}")
                return render(request, 'upload_combined.html')

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

                    birth_surname = company.findtext('ns:BirthSurname', default='', namespaces=ns)
                    trade_name = company.findtext('ns:CompanyData/ns:TradeName', default='', namespaces=ns)
                    registration_number = company.findtext('ns:CompanyData/ns:RegistrationNumber', default='', namespaces=ns)
                    customer_code = company.findtext('ns:CustomerCode', default='', namespaces=ns)
                    phone = company.findtext('ns:ContactsCompany/ns:CellularPhone', default='', namespaces=ns)
                    amount = command.findtext('.//ns:TotalLoanAmount', default='0', namespaces=ns)

                    print(f"Saving customer: {identifier}, {birth_surname}, {customer_code}, {phone}, {amount}")

                    SubmittedCustomerData.objects.update_or_create(
                        identifier=identifier,
                        defaults={
                            'trade_name': trade_name,
                            'registration_number': registration_number,
                            'customer_code': customer_code,
                            'phone': phone,
                            'birth_surname': birth_surname,
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

                # Create batch history record first since we'll need it for foreign key references
                batch_history = None
                if customer_batch_id:  # Only create if we have a valid batch ID
                    batch_history = BatchHistory.objects.create(
                        batch_identifier=customer_batch_id,
                        error_count=0,  # We'll update this later
                        uploaded_by=request.user,
                        filename=error_file.name
                    )

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

                        # Store customer code from matching submitted data
                        submitted_data = SubmittedCustomerData.objects.filter(identifier=identifier).first()
                        customer_code = submitted_data.customer_code if submitted_data else ''

                        if not existing_error:
                            # Create error with customer code included
                            # Ensure we use the batch history record created earlier
                            error = CustomerError.objects.create(
                                batch=batch_history,  # Use the BatchHistory object created earlier
                                identifier=identifier,
                                customer_name=submitted_data.birth_surname if submitted_data and submitted_data.birth_surname else customer_name,
                                customer_code=submitted_data.customer_code if submitted_data else customer_code,
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
                                customer_details={
                                    **customer_details,
                                    'birth_surname': submitted_data.birth_surname if submitted_data else '',
                                    'phone': submitted_data.phone if submitted_data else '',
                                }
                            )
                            # Store friendly message in customer_details_json
                            if hasattr(error, 'customer_details_json'):
                                error.customer_details_json = {'friendly_message': friendly_message}
                                error.save()
                            
                            error_count += 1
                            current_errors.append(error.id)
                
                # Update batch history with final error count
                if batch_history:
                    batch_history.error_count = error_count
                    batch_history.save()
                
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
            filename=error_file.name if error_file else "No file",
            customer_count=customer_count,
            error_count=error_count,
            error_ids=current_errors,
            is_active=True
        )

        # Note: We already created the batch history record earlier
        # No need to create it again here

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
    # Add at the beginning of the view
    # Clean up recent uploads if no errors exist
    recent_upload = RecentUpload.objects.filter(user=request.user, is_active=True).first()
    if recent_upload:
        # Check if any of the stored error IDs still exist
        existing_errors = CustomerError.objects.filter(id__in=recent_upload.error_ids).exists()
        if not existing_errors:
            # No errors exist anymore, delete the recent upload record
            recent_upload.delete()
            if 'recent_upload' in request.session:
                del request.session['recent_upload']

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
            
            # Get the customer code either from the error or submitted data
            customer_code = error.customer_code or (submitted.customer_code if submitted else '')
            
            # Use the error translator utility to get the friendly message
            from .error_translator_utils import process_dashboard_error
            friendly_message = process_dashboard_error(error.error_code, error.message)
            
            # Store the friendly message and customer code on the error object
            error.friendly_message = friendly_message
            error.customer_code = customer_code
                
            unique_errors[key] = {
                'error': error,
                'submitted': submitted,
                'customer_code': customer_code  # Add customer code to the context
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

@login_required
def validate_xml_file(request):
    """Validate XML file using comprehensive BOT rules and error checks"""
    if request.method == 'POST' and request.FILES.get('xml_file'):
        xml_file = request.FILES['xml_file']
        validation_errors = []
        
        try:
            content = xml_file.read()
            if content.startswith(b'\xef\xbb\xbf'):
                content = content[3:]
            xml_content = content.decode('utf-8-sig')

            root = ET.fromstring(xml_content)
            ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}

            for command in root.findall('.//ns:Command', ns):
                identifier = command.attrib.get('identifier', '')
                
                # Validate StorInstalment structure
                stor_instalment = command.find('.//ns:Cis.CB4.Projects.TZ.BOT.Body.Products.StorInstalment', ns)
                if stor_instalment is None:
                    validation_errors.append(f"Invalid command structure in Command {identifier}")
                    continue

                # Validate Instalment section
                instalment = stor_instalment.find('ns:Instalment', ns)
                if instalment is not None:
                    # Required Instalment fields
                    instalment_fields = {
                        'InstalmentCount': ('int', None),
                        'InstalmentType': ('lookup', 'InstalmentType.Fixed'),
                        'OutstandingAmount': ('decimal', None),
                        'PeriodicityOfPayments': ('lookup', None),
                        'TypeOfInstalmentLoan': ('lookup', 'TypeOfInstalmentLoan.BusinessLoan'),
                        'CurrencyOfLoan': ('lookup', 'Currency.TZS'),
                        'TotalLoanAmount': ('decimal', None),
                        'NegativeStatusOfLoan': ('lookup', 'NegativeStatusOfLoan.NoNegativeStatus'),
                        'PhaseOfLoan': ('lookup', 'PhaseOfLoan.Existing'),
                        'RescheduledLoan': ('lookup', 'Bool.False')
                    }

                    for field, (field_type, expected_value) in instalment_fields.items():
                        elem = instalment.find(f'ns:{field}', ns)
                        if elem is None or not elem.text:
                            validation_errors.append(f"Missing {field} in Command {identifier}")
                        elif expected_value and elem.text != expected_value:
                            validation_errors.append(f"Invalid {field} value in Command {identifier}")

                    # Validate ContractDates
                    contract_dates = instalment.find('ns:ContractDates', ns)
                    if contract_dates is not None:
                        for date_field in ['Start', 'ExpectedEnd', 'RealEnd']:
                            date_elem = contract_dates.find(f'ns:{date_field}', ns)
                            if date_elem is None or not elem.text:
                                validation_errors.append(f"Missing {date_field} date in Command {identifier}")

                # Validate ConnectedSubject
                connected_subject = instalment.find('.//ns:ConnectedSubject', ns)
                if connected_subject is not None:
                    company = connected_subject.find('.//ns:Company', ns)
                    if company is not None:
                        # Validate CompanyData
                        company_data = company.find('ns:CompanyData', ns)
                        if company_data is not None:
                            company_fields = {
                                'EstablishmentDate': ('datetime', None),
                                'LegalForm': ('lookup', 'LegalForm.GovernmentalInstitution'),
                                'RegistrationNumber': ('string', None),
                                'TradeName': ('string', None)
                            }

                            for field, (field_type, expected_value) in company_fields.items():
                                elem = company_data.find(f'ns:{field}', ns)
                                if elem is None or not elem.text:
                                    validation_errors.append(f"Missing {field} in Command {identifier}")
                                elif expected_value and elem.text != expected_value:
                                    validation_errors.append(f"Invalid {field} value in Command {identifier}")

                        # Validate AddressesCompany
                        addresses = company.find('.//ns:AddressesCompany/ns:Registration', ns)
                        if addresses is not None:
                            for field in ['Country', 'District', 'Region']:
                                elem = addresses.find(f'ns:{field}', ns)
                                if elem is None or not elem.text:
                                    validation_errors.append(f"Missing {field} in Command {identifier}")

                        # Validate ContactsCompany
                        contacts = company.find('ns:ContactsCompany', ns)
                        if contacts is not None:
                            phone = contacts.find('ns:CellularPhone', ns)
                            if phone is None or not phone.text:
                                validation_errors.append(f"Missing Phone Number in Command {identifier}")

                        # Validate CustomerCode
                        customer_code = company.findtext('ns:CustomerCode', '', ns)
                        if not customer_code.strip():
                            validation_errors.append(f"Missing CustomerCode in Command {identifier}")

                # Validate StorHeader
                header = stor_instalment.find('ns:StorHeader', ns)
                if header is None:
                    validation_errors.append(f"Missing StorHeader in Command {identifier}")
                else:
                    for field in ['Source', 'StoreTo', 'Identifier']:
                        elem = header.find(f'ns:{field}', ns)
                        if elem is None or not elem.text:
                            validation_errors.append(f"Missing {field} in StorHeader for Command {identifier}")

            validation_results = {
                'is_valid': len(validation_errors) == 0,
                'errors': validation_errors,
                'error_count': len(validation_errors),
                'filename': xml_file.name
            }

            if validation_errors:
                messages.error(request, f"Found {len(validation_errors)} validation errors.")
            else:
                messages.success(request, "XML file is valid and ready for BOT submission.")

        except ET.ParseError as parse_error:
            validation_errors.append(f"Invalid XML structure: {str(parse_error)}")
        except Exception as general_error:
            validation_errors.append(f"Validation error: {str(general_error)}")
        finally:
            return render(request, 'upload_combined.html', {'validation_results': validation_results})

    return redirect('upload_both_files')

@login_required
def resolve_all_batch(request):
    if request.method == 'POST':
        batch_id = request.POST.get('batch_id')
        print(f"Debug - Processing batch: {batch_id}")
        
        try:
            with transaction.atomic():
                # First try to get the batch record
                batch = BatchHistory.objects.filter(batch_identifier=batch_id).first()
                if not batch:
                    messages.error(request, f"Batch {batch_id} not found")
                    return redirect('batch_history')
                
                print(f"Debug - Found batch: {batch.batch_identifier}")
                
                # Get all pending errors for this batch
                pending_errors = CustomerError.objects.filter(
                    batch=batch,
                    status='pending'  # Make sure this matches your status choices
                )
                
                print(f"Debug - Found {pending_errors.count()} pending errors")
                
                if pending_errors.exists():
                    now = timezone.now()
                    
                    # Update all pending errors
                    update_count = pending_errors.update(
                        status='resolved',  # Make sure this matches your status choices
                        resolved_at=now,
                        resolved_by=request.user
                    )
                    
                    # Update batch status
                    batch.status = 'resolved'
                    batch.resolved_date = now
                    batch.save()
                    
                    messages.success(
                        request, 
                        f"Successfully resolved {update_count} errors from batch {batch_id}"
                    )
                    print(f"Debug - Updated {update_count} errors to resolved")
                else:
                    # Get all errors for this batch to check their statuses
                    all_errors = CustomerError.objects.filter(batch=batch)
                    status_counts = all_errors.values('status').annotate(
                        count=models.Count('status')
                    )
                    
                    print(f"Debug - Error status distribution: {list(status_counts)}")
                    
                    if all_errors.exists():
                        messages.warning(
                            request,
                            f"Found {all_errors.count()} errors but none are pending. "
                            f"Current status distribution: "
                            f"{', '.join([f'{s['status']}: {s['count']}' for s in status_counts])}"
                        )
                    else:
                        messages.warning(request, f"No errors found for batch {batch_id}")

        except Exception as e:
            messages.error(request, f"Error resolving batch: {str(e)}")
            import traceback
            print(f"Debug - Exception: {traceback.format_exc()}")

    return redirect('batch_history')

@login_required
def batch_history(request):
    batches = BatchHistory.objects.all().order_by('-upload_date')
    return render(request, 'batch_history.html', {'batches': batches})

@login_required
def upload_report(request):
    """Generate a CSV report of errors with optional batch filtering"""
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="error_report_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'},
    )
    
    writer = csv.writer(response)
    writer.writerow([
        'Batch ID',
        'Identifier',
        'Customer Name',  # This will contain company name or birth surname
        'Customer Code',
        'Error Code',
        'Error Message',
        'Status',
        'Upload Date',
        'Resolved Date'
    ])
    
    # Get batch filter if present
    batch_id = request.GET.get('batch')
    errors = CustomerError.objects.all()
    
    if batch_id:
        errors = errors.filter(xml_file_name__contains(batch_id))
    
    # Write error data
    for error in errors:
        submitted_data = SubmittedCustomerData.objects.filter(identifier=error.identifier).first()
        
        # First try to get trade name, if not available use birth surname
        customer_name = (submitted_data.trade_name if submitted_data and submitted_data.trade_name 
                        else (submitted_data.birth_surname if submitted_data and submitted_data.birth_surname 
                        else error.customer_name))
        
        writer.writerow([
            error.xml_file_name,
            error.identifier,
            customer_name,  # Modified to use the fallback logic
            submitted_data.customer_code if submitted_data else error.customer_code,
            error.error_code,
            error.message,
            error.get_status_display(),
            error.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            error.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if error.resolved_at else '-'
        ])
    
    return response

@login_required
def delete_batch(request, batch_id):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Fix: Change the filter to use correct lookup syntax
                CustomerError.objects.filter(
                    identifier__contains=batch_id
                ).delete()
                
                deleted = BatchHistory.objects.filter(
                    batch_identifier=batch_id
                ).delete()
                
                if deleted[0] > 0:
                    messages.success(request, f"Successfully deleted batch {batch_id}")
                else:
                    messages.warning(request, "Batch not found")
                
        except Exception as e:
            messages.error(request, f"Error deleting batch: {str(e)}")
    
    return redirect('batch_history')

@login_required
def extract_clean_entries(request, batch_id, format_type='xml'):
    try:
        # Get batch and its associated errors
        batch = BatchHistory.objects.filter(batch_identifier=batch_id).first()
        if not batch:
            messages.error(request, f"Batch {batch_id} not found")
            return redirect('batch_history')

        # Get clean entries from CustomerError model
        clean_entries = CustomerError.objects.filter(
            batch=batch,
            status='ok'
        )

        if not clean_entries.exists():
            messages.warning(request, "No clean entries found in this batch")
            return redirect('batch_history')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if format_type.lower() == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="clean_{batch_id}_{timestamp}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Identifier', 'Customer Name', 'Account Number', 'Amount', 'National ID'])
            
            for entry in clean_entries:
                writer.writerow([
                    entry.identifier,
                    entry.customer_name,
                    entry.account_number,
                    entry.amount,
                    entry.national_id
                ])
            return response
        else:
            # Create XML structure
            root = ET.Element('customers')
            for entry in clean_entries:
                customer = ET.SubElement(root, 'customer')
                ET.SubElement(customer, 'identifier').text = entry.identifier
                ET.SubElement(customer, 'customerName').text = entry.customer_name
                ET.SubElement(customer, 'accountNumber').text = entry.account_number
                ET.SubElement(customer, 'amount').text = str(entry.amount)
                ET.SubElement(customer, 'nationalId').text = entry.national_id
                ET.SubElement(customer, 'customerCode').text = entry.customer_code

            xml_str = ET.tostring(root, encoding='unicode', method='xml')
            response = HttpResponse(
                xml_str, 
                content_type='application/xml',
                headers={'Content-Disposition': f'attachment; filename="clean_{batch_id}_{timestamp}.xml"'}
            )
            return response

    except Exception as e:
        messages.error(request, f"Error extracting clean entries: {str(e)}")
        return redirect('batch_history')

def format_batch_id(identifier):
    """Format batch identifier to match required format (e.g., TZ06310411)"""
    # Remove any spaces or special characters
    clean_id = ''.join(filter(str.isalnum, identifier))
    # Ensure starts with TZ and is 10 characters
    if not clean_id.upper().startswith('TZ'):
        clean_id = 'TZ' + clean_id
    return clean_id[:10].upper()

def validate_personal_data(data):
    """Validate personal data fields and return any errors"""
    errors = []
    
    # Required fields validation
    if not data.get('birth_surname'):
        errors.append({
            'error_code': 'E_BIRTHSURNAME_MISSING',
            'message': 'Birth Surname is required',
            'severity': 'high'
        })
    
    if not data.get('customer_code'):
        errors.append({
            'error_code': 'E_CUSTOMERCODE_MISSING',
            'message': 'Customer Code is required',
            'severity': 'high'
        })
    
    phone = data.get('phone', '')
    if not phone:
        errors.append({
            'error_code': 'E_PHONE_MISSING',
            'message': 'Phone number is required',
            'severity': 'high'
        })
    elif not phone.startswith('+255'):
        errors.append({
            'error_code': 'E_PHONE_FORMAT',
            'message': 'Phone number must start with +255',
            'severity': 'medium'
        })

    try:
        loan_amount = float(data.get('loan_amount', '0'))
        if loan_amount <= 0:
            errors.append({
                'error_code': 'E_LOAN_AMOUNT_INVALID',
                'message': 'Loan amount must be greater than 0',
                'severity': 'high'
            })
    except ValueError:
        errors.append({
            'error_code': 'E_LOAN_AMOUNT_FORMAT',
            'message': 'Invalid loan amount format',
            'severity': 'high'
        })
    
    return errors

def get_header_identifier(xml_content):
    """Extract identifier from XML header with proper namespace handling"""
    try:
        root = ET.fromstring(xml_content.decode('utf-8'))
        
        # Try with namespace first
        ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}
        identifier = root.findtext('.//ns:Header/ns:Identifier', '', ns)
        
        # If not found, try without namespace
        if not identifier:
            identifier = root.findtext('.//Header/Identifier', '')
        
        return identifier.strip() if identifier else None
    except Exception as e:
        print(f"Error extracting header identifier: {e}")
        return None

def get_batch_identifier(content, is_customer_file=False):
    """Extract batch identifier from XML content based on file type"""
    try:
        # Handle UTF-8 BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
            
        root = ET.fromstring(content.decode('utf-8'))
        
        if is_customer_file:
            # Customer XML with namespace
            ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}
            
            # Try different paths for customer file
            paths = [
                './/ns:Header/ns:Identifier',  # With namespace
                './/Header/Identifier',        # Without namespace
            ]
            
            for path in paths:
                try:
                    identifier = root.findtext(path, '', namespaces=ns if 'ns:' in path else None)
                    if identifier:
                        return identifier.strip()
                except:
                    continue
        else:
            # BOT report XML - try multiple possible paths
            paths = [
                './/Header/Identifier',
                './/BatchResponse/Header/Identifier',
                './/Header/BatchId'
            ]
            
            for path in paths:
                try:
                    identifier = root.findtext(path)
                    if identifier:
                        return identifier.strip()
                except:
                    continue
        
        return None
        
    except Exception as e:
        print(f"XML Parsing Error: {str(e)}")
        print(f"Content start: {content[:200]}")  # Debug first 200 chars
        return None
@login_required
def upload_customer_xml(request):
    if request.method == 'POST':
        customer_file = request.FILES.get('customer_file')
        bot_report = request.FILES.get('bot_report')
        customer_count = 0
        error_count = 0
        current_errors = []
        
        # Add this block to extract batch ID
        customer_batch_id = None  # Initialize batch ID
        # Check batch identifiers
        if customer_file and bot_report:
            try:
                # Read customer file content
                customer_content = customer_file.read()
                if customer_content.startswith(b'\xef\xbb\xbf'):
                    customer_content = customer_content[3:]
                    
                # Read bot report content
                bot_content = bot_report.read()
                if bot_content.startswith(b'\xef\xbb\xbf'):
                    bot_content = bot_content[3:]

                # Get batch identifiers
                customer_batch_id = get_batch_identifier(customer_content, is_customer_file=True)
                bot_batch_id = get_batch_identifier(bot_content)

                # Validate batch identifiers
                if not customer_batch_id:
                    messages.error(request, "Could not find BatchIdentifier in customer file Header block")
                    return render(request, 'upload_customer.html')
                    
                if not bot_batch_id:
                    messages.error(request, "Could not find BatchIdentifier in BOT report Header block")
                    return render(request, 'upload_customer.html')

                # Compare identifiers
                if customer_batch_id != bot_batch_id:
                    messages.error(request, 
                        f"Batch identifiers do not match!\n"
                        f"Customer File: {customer_batch_id}\n"
                        f"BOT Report: {bot_batch_id}")
                    return render(request, 'upload_customer.html')

                # Reset file pointers
                customer_file.seek(0)
                bot_report.seek(0)

            except Exception as e:
                messages.error(request, f"Error checking batch identifiers: {str(e)}")
                return render(request, 'upload_customer.html')

        # ...rest of your existing code continues...

        # Clear session data
        if 'current_upload_errors' in request.session:
            del request.session['current_upload_errors']

        try:
            # Process customer XML
            customer_content = customer_file.read()
            if customer_content.startswith(b'\xef\xbb\xbf'):
                customer_content = customer_content[3:]
            
            customer_root = ET.fromstring(customer_content.decode('utf-8'))
            ns = {'ns': 'http://cb4.creditinfosolutions.com/BatchUploader/Batch'}

            # Process customer data and store it
            for command in customer_root.findall('.//ns:Command', ns):
                identifier = command.attrib.get('identifier', '')
                company = command.find('.//ns:Company', ns)
                if company is None:
                    continue

                birth_surname = company.findtext('ns:BirthSurname', default='', namespaces=ns)
                customer_code = company.findtext('ns:CustomerCode', default='', namespaces=ns)
                phone = company.findtext('.//ns:CellularPhone', default='', namespaces=ns)
                amount = command.findtext('.//ns:TotalLoanAmount', default='0', namespaces=ns)

                # Store customer data
                SubmittedCustomerData.objects.update_or_create(
                    identifier=identifier,
                    defaults={
                        'birth_surname': birth_surname,
                        'customer_code': customer_code,
                        'phone': phone,
                        'total_loan_amount': float(amount),
                        'submitted_by': request.user,
                    }
                )
                customer_count += 1

            # Process BOT report XML
            bot_content = bot_report.read()
            if bot_content.startswith(b'\xef\xbb\xbf'):
                bot_content = bot_content[3:]
            
            bot_root = ET.fromstring(bot_content.decode('utf-8'))
            
            # Create batch history
            batch_history = BatchHistory.objects.create(
                batch_identifier=customer_batch_id,
                error_count=0,
                uploaded_by=request.user,
                filename=bot_report.name
            )

            # Process errors from BOT report
            for command in bot_root.findall('.//Command'):
                identifier = command.attrib.get('identifier', '')
                
                for ex in command.findall('Exception'):
                    error_code = ex.findtext('ErrorCode') or 'UNKNOWN'
                    message = ''
                    line_number = ''
                    customer_details = {}
                    
                    # Extract error details from Parameters
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

                    # Set severity based on error code
                    severity = 'medium'
                    if error_code.startswith('E'):
                        severity = 'high'
                    elif error_code.startswith('W'):
                        severity = 'low'
                    elif error_code.startswith('C'):
                        severity = 'critical'

                    # Get submitted customer data
                    submitted_data = SubmittedCustomerData.objects.filter(identifier=identifier).first()

                    # Create error record
                    error = CustomerError.objects.create(
                        batch=batch_history,
                        identifier=identifier,
                        customer_name=submitted_data.birth_surname if submitted_data else '',
                        customer_code=submitted_data.customer_code if submitted_data else '',
                        phone=submitted_data.phone if submitted_data else '',
                        error_code=error_code,
                        message=message,
                        line_number=line_number,
                        severity=severity,
                        status='pending',
                        uploaded_by=request.user,
                        xml_file_name=bot_report.name,
                        customer_details={
                            **customer_details,
                            'birth_surname': submitted_data.birth_surname if submitted_data else '',
                            'phone': submitted_data.phone if submitted_data else '',
                        }
                    )
                    error_count += 1
                    current_errors.append(error.id)

            # Update batch history
            batch_history.error_count = error_count
            batch_history.save()

            # Update session data
            request.session['current_upload_errors'] = current_errors
            request.session['recent_upload'] = {
                'timestamp': timezone.now().isoformat(),
                'error_count': error_count,
                'customer_count': customer_count,
                'error_ids': current_errors,
                'filename': bot_report.name
            }

            # Create recent upload record
            RecentUpload.objects.create(
                user=request.user,
                filename=bot_report.name,
                customer_count=customer_count,
                error_count=error_count,
                error_ids=current_errors,
                is_active=True
            )

            messages.success(request, f"Upload completed. {customer_count} customer records and {error_count} errors saved.")
            return redirect('error_dashboard')

        except Exception as e:
            messages.error(request, f"Error processing files: {str(e)}")
            return redirect('upload_customer')

    return render(request, 'upload_customer.html')