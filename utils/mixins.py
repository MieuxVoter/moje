from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from vote.models import *
from django.views.generic.base import ContextMixin

class SupervisorTestMixin(UserPassesTestMixin):

    def test_func(self):
        if 'election_id' in self.kwargs:
            election_id = self.kwargs['election_id']
        else:
            election_id = self.kwargs['pk']
        election = get_object_or_404(Election, pk=election_id)
        self.supervisor = election.supervisor
        return self.supervisor and self.request.user == self.supervisor.user



class SupervisorFetchMixin(ContextMixin):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supervisor = get_object_or_404(Supervisor, user=self.request.user)
        context['supervisor'] = self.supervisor

        return context
