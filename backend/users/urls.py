from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # OTP endpoints
    path('auth/otp/request/', views.OTPRequestView.as_view(), name='otp_request'),
    path('auth/otp/verify/', views.OTPVerifyView.as_view(), name='otp_verify'),
    
    # Profile endpoints
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # Device management
    path('devices/', views.UserDeviceView.as_view(), name='user_device'),
    
    # Admin endpoints
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
]