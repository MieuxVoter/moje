from django.urls import path
from ws import views

urlpatterns = [
    path(r'sign-up/', views.sign_up, name='Sign up'),
    path(r'log-in/', views.log_in, name='Log in'),
    path(r'sign-in/', views.sign_in, name='Sign in'),
    path(r'reset-password/', views.reset_password, name='Reset password'),
    path(r'new-password/', views.new_password, name='New password')
 ]
