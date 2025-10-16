from rest_framework import status, viewsets
from rest_framework.viewsets import GenericViewSet 
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.db import transaction
from django.core.cache import cache
from . import models, serializers, throttling
from .utils import otp_utils, gmail_utils
import logging

logger = logging.getLogger('apps.users')

class OTPRequestView(APIView):
    """
    Request OTP code
    """
    permission_classes = [permissions.AllowAny]
    throttle_classes = [throttling.OTPThrottle]  
    
    def post(self, request):
        try:
            serializer = serializers.EmailSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            email = serializer.validated_data['email']
            otp = otp_utils.generate_otp()

            try:
                cache_key = f"otp_attempts:{email.lower()}"
                attempts = cache.get(cache_key, 0)
                if attempts >= 3:
                    return Response({"error": "Too many attempts"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

                cache.set(cache_key, attempts + 1, timeout=300)
                cache.set(f"otp_{email}", otp, timeout=300)
            except Exception as cache_error:
                logger.warning(f"Cache error: {cache_error}")
            
            email_sent = gmail_utils.send_otp_email(email, otp, async_send=False)
            if not email_sent:
                return Response({"error": "Failed to send OTP email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({"message": "OTP sent"}, status=status.HTTP_200_OK)
        
        except serializers.ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"OTP request failed: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class OTPVerifyView(APIView):
    """
    Verify otp code
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            serializer = serializers.OTPVerifySerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                cached_otp = cache.get(f"otp_{email}")
                
                if not cached_otp:
                    return Response({"error": "OTP expired or not found"}, status=status.HTTP_404_NOT_FOUND)

                if cached_otp != otp_code:
                    return Response({"error": "Incorrect OTP"}, status=status.HTTP_400_BAD_REQUEST)
                
                cache.set(f"verified_{email}", True, timeout=600)
                cache.delete(f"otp_{email}")
            except Exception as cache_error:
                logger.warning(f"Cache error during OTP verification: {cache_error}")
                return Response({"error": "Cache error, please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
            
        except serializers.ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UserRegisterView(APIView):
    """
    A viewset for registering new users.
    """
    permission_classes = [permissions.AllowAny]
    
    @transaction.atomic
    def post(self, request):
        serializer = serializers.UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        
        try:
            verified = cache.get(f"verified_{email}")
            if not verified:
                return Response({"error": "Please verify your email first"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as cache_error:
            logger.warning(f"Cache error during registration: {cache_error}")
            return Response({"error": "Cache error, please try again"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if models.User.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = models.User.objects.create_user(
            email=email,
            username=username,  
            password=password
        )
        
        try:
            cache.delete(f"verified_{email}")
        except Exception as cache_error:
            logger.warning(f"Cache error clearing verification: {cache_error}")
        
        gmail_utils.send_welcome_email(email, username, async_send=False)
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'User registered successfully',
            'user': serializers.UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'next_step': 'complete_profile'
        }, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return models.User.objects.select_related('profile').filter(id=self.request.user.id)
        
    def update(self, request, *args, **kwargs):
        if request.user.id != int(kwargs['pk']):
            return Response({"error": "You can only update your own account"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        try:
            key = f"user_{request.user.id}"
            data = cache.get(key)
            if not data:
                serializer = self.get_serializer(request.user)
                data = serializer.data
                cache.set(key, data, timeout=60)
            return Response(data)
        except Exception as cache_error:
            logger.warning(f"Cache error in me view: {cache_error}")
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

class CompleteProfileView(APIView):
    """
    A viewset for completing user profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = models.User.objects.select_related('profile').get(id=request.user.id)
        profile = user.profile

        serializer = serializers.CompleteProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.first_name = serializer.validated_data['first_name']
        user.last_name = serializer.validated_data['last_name']
        user.save()

        for field in ['city', 'country', 'date_birth', 'avatar']:
            if field in serializer.validated_data:
                setattr(profile, field, serializer.validated_data[field])
        profile.save()

        user.refresh_from_db()
        return Response({
            'message': 'Profile completed successfully',
            'user': serializers.UserSerializer(user).data,
            'profile_complete': True
        }, status=status.HTTP_200_OK)
    
    def get(self, request):
        user = models.User.objects.select_related('profile').get(id=request.user.id)
        profile = user.profile
        is_complete = all([
            user.first_name,
            user.last_name,
            profile.city,
            profile.country,
            profile.date_birth
        ])
        return Response({
            'profile_complete': is_complete,
            'user': serializers.UserSerializer(user).data,
            'profile': serializers.ProfileSerializer(profile).data if is_complete else None
        })
        
class CheckProfileStatusView(APIView):
    """ 
    A viewset for checking if user profile is complete.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            user = models.User.objects.select_related('profile').get(id=request.user.id)
            profile = user.profile
            is_complete = all([
                user.first_name,
                user.last_name,
                profile.city,
                profile.country,
                profile.date_birth
            ])
            
            return Response({
                'profile_complete': is_complete,
                'user': serializers.UserSerializer(request.user).data,
                'profile': serializers.ProfileSerializer(profile).data if is_complete else None
            })
        except models.Profile.DoesNotExist:
            return Response({
                'profile_complete': False,
                'user': serializers.UserSerializer(request.user).data
            })

class ChangePasswordViewSet(GenericViewSet):
    """
    A viewset for changing user password.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ChangePasswordSerializer
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)
    
