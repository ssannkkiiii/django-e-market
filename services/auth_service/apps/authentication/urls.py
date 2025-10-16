from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('google-login/', views.GoogleLoginInitView.as_view(), name='google-login'),
    path('google-callback/', views.GoogleAuthCallbackView.as_view(), name='google-callback')
]
