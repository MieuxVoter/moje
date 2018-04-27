from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import available_attrs, method_decorator

from datetime import datetime

from vote.models import *
from majority_judgment.tools import *


@login_required
def redirect_results(request):
    try:
        voter       = Voter.objects.get(user=request.user)
        election_id = voter.election.pk
        return HttpResponseRedirect('/results/{:d}/'.format(election_id))
    except Voter.DoesNotExist:
        return render(request, 'error.html', {"error":"Nous n'avons pas trouvé d'élections pour vous..."})


@login_required
def results(request, election_id):
    election = get_object_or_404(Election, pk=election_id)
    supervisor = None
    params = {}

    # close election according to date
    if election.end and election.end < datetime.now().date():
        election.state = Election.OVER
        election.save()

    # check access rights
    if election.supervisor.user == request.user:
        supervisor = election.supervisor
        params["supervisor"] = supervisor
    elif not Voter.objects.filter(user=request.user, election=election).exists():
        return render(request, 'vote/error.html',
                {'error': "Vous n'avez pas accès à cette élection.", "election":election})
    elif election.state != Election.OVER:
        return render(request, 'vote/error.html',
                {'error': "L'élection n'est pas terminée", "election":election})
    else:
        voter = Voter.objects.get(user=request.user, election=election)
        params["voter"] = voter


    # read database
    grades  = [g.name for g in Grade.objects.filter(election=election)]
    ratings = get_ratings(election)
    results = []
    cs      = Candidate.objects.filter(election=election)
    Nvotes  = len(Rating.objects.filter(election=election))

    if Nvotes == 0:
        template = "election" if supervisor else "vote"
        return render(request, template + "/error.html", {'error':"Les urnes sont vides.", "election":election})

    for i in range(len(cs)):
        result = Result(candidate=cs[i],
                        ratings=ratings[i, :],
                        grades=grades)
        results.append(result)

    # ranking according to the majority judgment
    ranking = [r.candidate for r in majority_judgment(results)]

    params['ranking'] = ranking
    params["nvotes"] = Nvotes
    params["election_id"] = election_id
    params["election"] = election
    return render(request, 'vote/results.html', params)
