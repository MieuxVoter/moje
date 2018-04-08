from django.urls import path
from django.contrib.auth import views as auth_views
from vote import views

urlpatterns = [
    path(r'vote/<int:id_election>/', views.vote, name='vote'),
    path(r'vote/', views.redirect_vote, name='vote'),
    path(r'candidates/<int:id_election>/', views.CandidateList.as_view(), name='candidates'),
    path(r'candidates/', views.redirect_candidates, name='candidates'),
    path(r'results/<int:id_election>/', views.results, name='results'),
    path(r'results/', views.redirect_results, name='results'),
    path(r'voter/<int:pk>', views.voter_detail, name='voter'),
    path(r'candidate/<int:pk>',
            views.CandidateDetail.as_view(),
            name='candidate')
 ]
