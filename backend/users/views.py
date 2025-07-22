from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import random
import logging

from .models import User, OTPVerification, UserDevice
from .serializers import (
    UserRegistrationSerializer, OTPRequestSerializer, OTPVerificationSerializer,
    LoginSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    PasswordChangeSerializer, UserDeviceSerializer, AdminUserListSerializer
)
from .utils import send_sms_otp

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send OTP for phone verification if phone provided
        if user.phone:
            self.send_verification_otp(user, user.phone)
        
        return Response({
            'message': 'Registration successful. Please verify your phone number.',
            'user_id': user.id,
            'requires_phone_verification': bool(user.phone)
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_otp(self, user, phone):
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices('0123456789', k=6))
        
        # Create OTP record
        OTPVerification.objects.create(
            user=user,
            otp_code=otp_code,
            phone_number=phone,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send SMS (implement actual SMS sending)
        send_sms_otp(phone, otp_code, 'registration')


class OTPRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        purpose = serializer.validated_data['purpose']
        
        # Find user by phone
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this phone number not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate and send OTP
        otp_code = ''.join(random.choices('0123456789', k=6))
        
        OTPVerification.objects.create(
            user=user,
            otp_code=otp_code,
            phone_number=phone,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        send_sms_otp(phone, otp_code, purpose)
        
        return Response({
            'message': f'OTP sent to {phone}',
            'expires_in': 600  # 10 minutes
        })


class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data['purpose']
        
        try:
            otp = OTPVerification.objects.get(
                phone_number=phone,
                otp_code=otp_code,
                purpose=purpose,
                is_used=False
            )
            
            if otp.is_expired:
                return Response(
                    {'error': 'OTP has expired.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            # Update user verification status
            user = otp.user
            if purpose in ['registration', 'phone_verification']:
                user.phone_verified = True
                user.save()
            
            # Generate tokens for login purposes
            if purpose in ['registration', 'login']:
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'OTP verified successfully.',
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'user': UserProfileSerializer(user).data
                })
            
            return Response({'message': 'OTP verified successfully.'})
            
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Update last login
        user.last_login = timezone.now()
        user.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserProfileSerializer(user).data
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully.'})


class UserDeviceView(generics.CreateAPIView):
    serializer_class = UserDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Mark user device as inactive if device_id provided
            device_id = request.data.get('device_id')
            if device_id:
                UserDevice.objects.filter(
                    user=request.user,
                    device_id=device_id
                ).update(is_active=False)
            
            return Response({'message': 'Logged out successfully.'})
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return Response({'message': 'Logged out successfully.'})


# Admin views
class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserListSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'is_active', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering_fields = ['date_joined', 'last_login']


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_user_status(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        return Response({
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully.',
            'is_active': user.is_active
        })
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
