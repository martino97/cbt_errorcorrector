from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from core import views

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
    
    # Original dashboard path (if you still need it)
    path('dashboard/', login_required(views.error_dashboard), name='error_dashboard'),
]