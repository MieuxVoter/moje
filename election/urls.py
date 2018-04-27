from django.urls import path
from django.contrib.auth import views as auth_views
from election import views

urlpatterns = [
    path(r'manage/general/', views.create_election, name="general"),
    path(r'manage/general/<int:election_id>/', views.general_step, name="general"),
    # path(r'manage/config/<int:election_id>/', views.config_step, name="config"),
    path(r'manage/voters/<int:election_id>/', views.voters_step, name="voters"),
    path(r'<int:election_id>/', views.election_detail, name='election'),
    path(r'<int:election_id>', views.election_detail, name='election'),
    path(r'', views.redirect_election, name='vote'),

    # candidate
    path(r'manage/candidates/<int:election_id>/',
            views.candidates_step,
            name="candidates"
        ),
    path(r'ajax/create_candidate/',
            views.create_candidate,
            name="create_candidate"
        ),
    path(r'manage/delete_candidate/<int:pk>/',
                views.CandidateDelete.as_view(),
                name="delete_candidate"
        ),


    # voter
    path(r'manage/voters/<int:election_id>/',
            views.candidates_step,
            name="voters"
        ),
    path(r'ajax/create_voter/',
            views.create_voter,
            name="create_voter"
        ),
    path(r'manage/delete_voter/<int:pk>/',
                views.VoterDelete.as_view(),
                name="delete_voter"
        ),

    path(r'dashboard/', views.ElectionList.as_view(), name='dashboard'),
    path(r'manage/delete_election/<int:pk>/',
                views.ElectionDelete.as_view(),
                name="delete_election"
        ),

    path(r'launch/<int:pk>/',
                views.launch_election,
                name="launch_election"
        ),

    path(r'close/<int:pk>/',
                views.close_election,
                name="close_election"
        ),

 ]
