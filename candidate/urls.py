from django.urls import path
from django.contrib.auth import views as auth_views

from candidate import views

urlpatterns = [
    path(r'<int:election_id>/', views.CandidateList.as_view(), name='candidates'),
    path(r'', views.redirect_candidates, name='candidates'),
    path(r'detail/<int:pk>',
            views.CandidateDetail.as_view(),
            name='candidate')
 ]
