from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import available_attrs, method_decorator
from django.utils.translation import gettext_lazy as _

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

    # close election according to date
    # if election.end and election.end < datetime.now().date():
    #     election.state = Election.OVER
    #     election.save()

    # check access rights
    try:
        supervisor = Supervisor.objects.get(election=election, user=request.user)
        params["supervisor"] = supervisor
    except Supervisor.DoesNotExist:
        supervisor = None

        if not Voter.objects.filter(user=request.user,
                                  election=election).exists():
            return render(request, 'vote/error.html',
                {'error': "You have no access to this election.", "election":election})
        elif election.state != Election.OVER:
            return render(request, 'vote/error.html',
                    {'error': "The election is not over", "election":election})
        else:
            voter = Voter.objects.get(user=request.user, election=election)
            params["voter"] = voter


    # fetch results
    grades = [g.name for g in Grade.objects.filter(election=election)]
    ratings = get_ratings(election)
    ratings = np.array(ratings, dtype=int)
    results = []
    candidates = Candidate.objects.filter(election=election)
    Nvotes = len(Rating.objects.filter(election=election))

    if Nvotes == 0:
        template = "election" if supervisor else "vote"
        return render(request, template + "/error.html",
                        {'error':"No vote has already been casted.", "election":election})

    for i, candidate in enumerate(candidates):
        result = Result(candidate=candidate,
                        ratings=ratings[i, :],
                        grades=grades)
        results.append(result)

    # ranking according to the majority judgment
    ranking = []
    for r in majority_judgment(results):
        candidate = r.candidate
        candidate.ratings = r.ratings
        candidate.median = grades[arg_median(ratings[i,:])]
        ranking.append(candidate)

    params['ranking'] = ranking
    params["nvotes"] = Nvotes
    params["election_id"] = election_id
    params["election"] = election
    params["grades"] = grades
    return render(request, 'vote/results.html', params)
