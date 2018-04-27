from django.urls import path
from django.contrib.auth import views as auth_views
from majority_judgment import views

urlpatterns = [
    path(r'charts/results-<int:election_id>.png', views.chart_results, name='results'),
]
