from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from core import views

urlpatterns = [
    path('', login_required(views.home), name='home'),
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='password_reset.html'
    ), name='password_reset'),
    path('upload_report/', views.upload_report, name='upload_report'),
    path('error_dashboard/', views.error_dashboard, name='error_dashboard'),
    path('update_error_status/<int:error_id>/', views.update_error_status, name='update_error_status'),
    path('error/<int:error_id>/', views.error_detail, name='error_detail'),
    path('error/<int:error_id>/update/', views.update_error_status, name='update_error_status'),
    
]
