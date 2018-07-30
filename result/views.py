from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import available_attrs, method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import EmptyResultSet

from datetime import datetime

from vote.models import *
from majority_judgment.tools import *


@login_required
def redirect_results(request):
    try:
        voter = Voter.objects.get(user=request.user)
        election_id = voter.election.pk
        return HttpResponseRedirect('/results/{:d}/'.format(election_id))
    except Voter.DoesNotExist:
        return render(request, 'error.html', {"error":"No election has been found for you..."})


@login_required
def results(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    supervisor = None
    params = {}

    # check access rights
    try:
        supervisor = Supervisor.objects.get(election=election, user=request.user)
        params["supervisor"] = supervisor
    except Supervisor.DoesNotExist:
        supervisor = None

        if not Voter.objects.filter(user=request.user,
                                  election=election).exists():
            return render(request, 'vote/error.html',
                {'error': _("You have no access to this election."), "election":election})
        elif election.state != Election.OVER:
            return render(request, 'vote/error.html',
                    {'error': _("The election is not over"), "election":election})
        else:
            voter = Voter.objects.get(user=request.user, election=election)
            params["voter"] = voter


    # fetch results
    try:
        ranking = get_ranking(election_id)
    except EmptyResultSet:
        return render(request, 'election/error.html',
                {'error': _("No vote has already been casted."), "election":election})

    grades = [g.name for g in Grade.objects.filter(election=election)]
    Nvotes = sum([candidate.ratings for candidate in ranking])

    params['ranking'] = ranking
    params["nvotes"] = Nvotes
    params["election_id"] = election_id
    params["election"] = election
    params["grades"] = grades
    return render(request, 'result/results.html', params)
