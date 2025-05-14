from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Main dashboard - now points to customer_error_dashboard
    path('', login_required(views.customer_error_dashboard), name='customer_error_dashboard'),
    
    # Auth related paths
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html'
    ), name='password_reset'),
    
    # File upload path
    path('upload/', views.upload_both_files, name='upload_both_files'),
    path('upload-customer/', views.upload_customer_xml, name='upload_customer'),
    
    # Original dashboard path (if you still need it)
    path('dashboard/', login_required(views.error_dashboard), name='error_dashboard'),
    path('upload-report/', views.upload_report, name='upload_report'),
    path('documentation/', login_required(views.documentation_view), name='documentation'),
    
    path('validate-xml/', views.validate_xml_file, name='validate_xml'),

    path('resolve-batch/', views.resolve_all_batch, name='resolve_all_batch'),
    path('batch-history/', views.batch_history, name='batch_history'),
    path('delete-batch/<str:batch_id>/', views.delete_batch, name='delete_batch'),
    path('error-dashboard/', views.error_dashboard, name='error_dashboard'),

    path('extract-clean/<str:batch_id>/', 
         views.extract_clean_entries, 
         name='extract_clean_entries'),
    path('extract-clean/<str:batch_id>/<str:format_type>/', 
         views.extract_clean_entries, 
         name='extract_clean_entries'),

    path('coop-validator/', views.coop_validator, name='coop_validator'),
    # path('download-clean-xml/<int:batch_id>/', views.download_clean_xml, name='download_clean_xml'),
    path('download_clean_xml/<int:batch_id>/', views.download_clean_xml, name='download_clean_xml'),
    path('upload_report/', views.upload_report, name='upload_report'),
   ]