from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from . import models

class EmailSerializer(serializers.Serializer):
    """
    Email serializer for email validation
    """
    email = serializers.EmailField(validators=[validate_email])
    
class OTPVerifySerializer(serializers.Serializer):
    """
    Serializer for otp verify
    """
    email = serializers.EmailField(validators=[validate_email])
    otp_code = serializers.CharField(max_length=6, min_length=6)

    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value
    
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(
        write_only=True, 
        validators=[validate_password],
        min_length=8,
        help_text="Password must be at least 8 characters long"
    )    
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = models.User
        fields = ['email', 'username', 'password', 'password_confirm']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords must match"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = models.User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model
    """
    class Meta:
        model = models.Profile
        fields = ['avatar', 'city', 'country', 'date_birth']

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    profile = ProfileSerializer(required=False)

    class Meta:
        model = models.User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(update_fields=validated_data.keys())

        if profile_data:
            profile, _ = models.Profile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save(update_fields=profile_data.keys())

        return instance

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value
    
    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("New passwords do not match")
        validate_password(data['new_password'], self.context['request'].user)
        return data
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    
class CompleteProfileSerializer(serializers.Serializer):
    """
    Serializer for completing user profile
    """
    first_name = serializers.CharField(max_length=30, required=True)
    last_name = serializers.CharField(max_length=30, required=True)
    city = serializers.CharField(max_length=100, required=True)
    country = serializers.CharField(max_length=100, required=True)
    date_birth = serializers.DateField(required=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required")
        return value.strip()

    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required")
        return value.strip()

    def validate_city(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("City is required")
        return value.strip()

    def validate_country(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Country is required")
        return value.strip()

    def validate_date_birth(self, value):
        from datetime import date
        if value and value >= date.today():
            raise serializers.ValidationError("Date of birth must be in the past")
        return value