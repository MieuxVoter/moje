from django.conf.urls import url
from django.contrib.auth import views as auth_views
from vote import views

urlpatterns = [
     url(r'^$', views.vote, name='vote'),
     url(r'^candidates/$', views.CandidateList.as_view(), name='candidates'),
     url(r'^results/$', views.results, name='results'),
     url(r'^voter/(?P<pk>\d+)$', views.VoterDetail.as_view(), name='voter'),
     url(r'^candidate/(?P<pk>\d+)$',
            views.CandidateDetail.as_view(),
            name='candidate')
 ]
