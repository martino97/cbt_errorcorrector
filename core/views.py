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
from .models import SubmittedCustomerData, CustomerError


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

                        # Check if this error already exists for this identifier
                        existing_error = CustomerError.objects.filter(
                            identifier=identifier, 
                            error_code=error_code,
                            message=message,
                            status='pending'  # Only check pending errors to allow resolved ones to be recreated
                        ).first()

                        if not existing_error:
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
                                customer_details=customer_details,
                                upload_session=upload_session_id
                            )
                            error_count += 1
                            current_errors.append(error.id)
                
                # Store current upload session errors in session
                request.session['current_upload_errors'] = current_errors
                
            except Exception as e:
                messages.error(request, f"Failed to process error file: {e}")

        messages.success(request, f"Upload completed. {customer_count} customer records and {error_count} errors saved.")
        return redirect('customer_error_dashboard')

    return render(request, 'upload_combined.html')


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
            # Try to find the customer data by identifier
            submitted = SubmittedCustomerData.objects.filter(identifier=error.identifier).first()
            unique_errors[key] = {
                'error': error,
                'submitted': submitted
            }
    
    # Convert to list for template
    data = list(unique_errors.values())
    
    context = {
        'data': data,
        'error_stats': {
            'total': total_errors,
            'pending': pending_errors,
            'resolved': resolved_errors,
            'ignored': ignored_errors
        },
        'current_upload': {
            'customer_count': 0,
            'error_count': current_upload_count,
            'current_upload_errors': current_upload_count
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