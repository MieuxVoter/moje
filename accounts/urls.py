from django.urls import path

from . import views


urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path('redirect/', views.redirect_login, name='redirect_login'),
    path('profile/<int:pk>/', views.user_detail, name='redirect_login'),
]
