from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPVerification, UserDevice


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'is_active', 'phone_verified', 'date_joined']
    list_filter = ['role', 'is_active', 'is_verified', 'phone_verified', 'country']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'gender', 'profile_image')}),
        ('Location', {'fields': ('city', 'country')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Verification', {'fields': ('is_verified', 'phone_verified', 'email_verified')}),
        ('Preferences', {'fields': ('preferred_language', 'preferred_currency', 'marketing_consent')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'purpose', 'is_used', 'created_at', 'expires_at']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__email', 'phone_number']
    readonly_fields = ['created_at', 'expires_at']


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'platform', 'is_active', 'created_at', 'last_seen']
    list_filter = ['platform', 'is_active']
    search_fields = ['user__email', 'device_name', 'device_id']
    readonly_fields = ['created_at', 'last_seen']
