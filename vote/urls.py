from django.urls import path
from django.contrib.auth import views as auth_views
from vote import views

urlpatterns = [
    path(r'<int:election_id>/', views.vote, name='vote'),
    path(r'', views.redirect_vote, name='vote'),
    path(r'success/<int:pk>', views.success, name='success'),
 ]
