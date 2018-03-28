from django.conf.urls import url
from django.contrib.auth import views as auth_views
from majority_judgment import views

urlpatterns = [
    url(r'^charts/results.png$', views.chart_results, name='results'),
]
