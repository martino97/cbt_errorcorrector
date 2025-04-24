from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.utils import timezone
import xml.etree.ElementTree as ET
from io import BytesIO
from .models import CustomerError

@login_required
def home(request):
    return render(request, 'index.html')

def register_user(request):
    if request.user.is_authenticated:
        return redirect('home')

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
def upload_report(request):
    if request.method == 'POST' and request.FILES.get('xml_file'):
        xml_file = request.FILES['xml_file']
        try:
            file_content = xml_file.read()
            if file_content.startswith(b'\xef\xbb\xbf'):
                file_content = file_content[3:]

            root = ET.fromstring(file_content.decode('utf-8'))
            error_count = 0

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

                exceptions = command.findall('Exception')
                if exceptions:
                    for ex in exceptions:
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

                        CustomerError.objects.create(
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
                            xml_file_name=xml_file.name,
                            customer_details=customer_details
                        )
                        error_count += 1

            if error_count > 0:
                messages.success(request, f"XML file processed successfully. {error_count} errors found and saved.")
            else:
                messages.info(request, "XML file processed, but no errors were found.")
            return redirect('error_dashboard')

        except ET.ParseError as pe:
            messages.error(request, f"Invalid XML format: {str(pe)}")
        except UnicodeDecodeError:
            messages.error(request, "File encoding not supported. Please use UTF-8 encoding.")
        except Exception as e:
            messages.error(request, f"Error processing XML file: {str(e)}")
    else:
        if request.method == 'POST':
            messages.error(request, "No XML file selected.")

    return redirect('home')

@login_required
def error_dashboard(request):
    errors = CustomerError.objects.all()
    
    status = request.GET.get('status')
    if status:
        errors = errors.filter(status=status)

    severity = request.GET.get('severity')
    if severity:
        errors = errors.filter(severity=severity)

    search = request.GET.get('search')
    if search:
        errors = errors.filter(
            models.Q(customer_name__icontains=search) |
            models.Q(account_number__icontains=search) |
            models.Q(error_code__icontains=search) |
            models.Q(national_id__icontains=search)
        )

    context = {
        'critical_count': CustomerError.objects.filter(severity='critical').count(),
        'high_count': CustomerError.objects.filter(severity='high').count(),
        'medium_count': CustomerError.objects.filter(severity='medium').count(),
        'low_count': CustomerError.objects.filter(severity='low').count(),
    }

    paginator = Paginator(errors.order_by('-created_at'), 15)
    page = request.GET.get('page')
    try:
        customers = paginator.page(page)
    except PageNotAnInteger:
        customers = paginator.page(1)
    except EmptyPage:
        customers = paginator.page(paginator.num_pages)

    context['customers'] = customers
    return render(request, 'dashboard_errors.html', context)

@login_required
def error_detail(request, error_id):
    try:
        error = CustomerError.objects.get(id=error_id)
        context = {'error': error}
        return render(request, 'error_detail.html', context)
    except CustomerError.DoesNotExist:
        messages.error(request, "Error not found.")
        return redirect('error_dashboard')

@login_required
def update_error_status(request, error_id):
    if request.method == 'POST':
        try:
            error = CustomerError.objects.get(id=error_id)
            status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            if status:
                error.status = status
                error.notes = notes
                if status == 'resolved' and error.status != 'resolved':
                    error.resolved_by = request.user
                    error.resolved_at = timezone.now()
                error.save()
                messages.success(request, f"Error status updated to {error.get_status_display()}.")
            else:
                messages.error(request, "No status provided.")
        except CustomerError.DoesNotExist:
            messages.error(request, "Error not found.")
        except Exception as e:
            messages.error(request, f"Error updating status: {str(e)}")

    return redirect('error_dashboard')
