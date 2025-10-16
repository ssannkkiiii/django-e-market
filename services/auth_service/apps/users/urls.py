from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'users'

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('request-otp/', views.OTPRequestView.as_view(), name='request-otp'),
    path('verify-otp/', views.OTPVerifyView.as_view(), name='verify-otp'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('complete-profile/', views.CompleteProfileView.as_view(), name='complete-profile'),
    path('profile-status/', views.CheckProfileStatusView.as_view(), name='profile-status'),
    path('change-password/', views.ChangePasswordViewSet.as_view({'post': 'change_password'})),
    path('', include(router.urls)),
]
