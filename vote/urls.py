from django.urls import path
from django.contrib.auth import views as auth_views
from vote import views

urlpatterns = [
    path(r'vote/<int:id_election>/', views.vote, name='vote'),
    path(r'candidates/', views.CandidateList.as_view(), name='candidates'),
    path(r'results/<int:pk>', views.results, name='results'),
    path(r'voter/<int:pk>', views.VoterDetail.as_view(), name='voter'),
    path(r'candidate/<int:pk>',
            views.CandidateDetail.as_view(),
            name='candidate')
 ]
