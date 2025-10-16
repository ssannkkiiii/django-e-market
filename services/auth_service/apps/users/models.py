from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from . import managers

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that supports using email instead of username
    """
    class UserRoleChoice(models.TextChoices):
        CLIENT = "client", "Client"
        ADMIN = "admin", "Admin"
        VENDOR = "vendor", "Vendor"
        
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    last_name = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    role = models.CharField(
        max_length=10,
        choices=UserRoleChoice,
        default=UserRoleChoice.CLIENT
        )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    objects = managers.UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def become_vendor(self):
        self.role = self.UserRoleChoice.VENDOR
        self.save()
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

class Profile(models.Model):
    """
    User profile model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    date_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = 'profile'
        verbose_name_plural = 'profiles'
        indexes = [
            models.Index(fields=['user']),
        ]
