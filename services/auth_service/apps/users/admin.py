from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from . import models

@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for User model
    """
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']

@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for Profile model
    """
    list_display = ['user', 'city', 'country', 'date_birth', 'avatar_preview']
    list_filter = ['city', 'country', 'date_birth']
    search_fields = ['user__email', 'user__username', 'city', 'country']
    raw_id_fields = ['user']
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.avatar.url)
        return "No avatar"
    avatar_preview.short_description = "Avatar"
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal Info', {'fields': ('city', 'country', 'date_birth')}),
        ('Avatar', {'fields': ('avatar',)}),
    )