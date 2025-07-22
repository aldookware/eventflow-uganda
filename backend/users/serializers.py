from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, OTPVerification, UserDevice
import random
import string


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'phone', 'first_name', 'last_name', 
            'password', 'password_confirm', 'role', 'city',
            'preferred_language', 'marketing_consent'
        ]
        extra_kwargs = {
            'role': {'default': 'user'}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    purpose = serializers.ChoiceField(choices=[
        ('registration', 'Registration'),
        ('login', 'Login'), 
        ('password_reset', 'Password Reset'),
        ('phone_verification', 'Phone Verification'),
    ])


class OTPVerificationSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    otp_code = serializers.CharField(max_length=6)
    purpose = serializers.CharField(max_length=20)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'full_name',
            'role', 'date_of_birth', 'gender', 'profile_image', 'city', 'country',
            'is_verified', 'phone_verified', 'email_verified', 'date_joined',
            'preferred_language', 'preferred_currency', 'marketing_consent'
        ]
        read_only_fields = ['id', 'email', 'role', 'is_verified', 'date_joined']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 
            'profile_image', 'city', 'preferred_language', 'marketing_consent'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match.")
        return attrs


class UserDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDevice
        fields = ['device_id', 'device_name', 'platform', 'fcm_token']
        
    def create(self, validated_data):
        user = self.context['request'].user
        device, created = UserDevice.objects.update_or_create(
            user=user,
            device_id=validated_data['device_id'],
            defaults=validated_data
        )
        return device


class AdminUserListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'full_name', 'role', 'city', 'country',
            'is_active', 'is_verified', 'phone_verified', 'email_verified', 
            'date_joined', 'last_login'
        ]