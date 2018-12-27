from django.urls import path
from belenios import views

urlpatterns = [
    path(r'election/create/', views.election_create, name='Create election'),
    path(r'election/voter/add/', views.election_voter_add, name='Add voter to election'),
    path(r'vote/create/', views.vote_create, name='Create vote'),
    path(r'election/close/', views.close_election, name='Close election'),
    path(r'election/delete/', views.delete_election, name='Delete election'),
    path(r'election/information/', views.election_information, name='Election information'),
    path(r'election/detail/', views.election_detail, name='Election detail'),
    path(r'supervisor/election/list/', views.supervisor_election_list, name='supervisor election list'),
    path(r'supervisor/election/result/', views.supervisor_election_result, name='supervisor election result'),


]
