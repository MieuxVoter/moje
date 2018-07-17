from django.urls import path, include

from . import views


urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('redirect/', views.redirect_login, name='redirect_login'),
    path('profile/<int:pk>/', views.user_detail, name='redirect_login'),
]
