from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.auth import views as auth_views

from result import views

urlpatterns = [
    path(r'<int:election_id>/', views.results, name='results'),
    path(r'<int:election_id>', views.results, name='results'),
    path(r'', views.redirect_results, name='results'),
    ]
