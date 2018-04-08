from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect

from vote.models import *
from vote.forms import *
from majority_judgment.tools import *


class CandidateList(generic.ListView):
    model = Candidate

class CandidateDetail(generic.DetailView):
    model = Candidate

class VoterDetail(generic.DetailView):
    model = Voter


def vote(request, id_election):
    election    = get_object_or_404(Election, pk=id_election)
    form = VoteForm(request.POST or None, election=election)

    if form.is_valid():
        # FIXME: use the real voter
        voter = Voter.objects.first()

        # FIXME: check whether the voter has already casted a vote
        for c, g in form_grades(form, election).items():
            r = Rating(candidate=c, grade=g, voter=voter, election=election)
            r.save()
        return HttpResponseRedirect('/results/{:d}'.format(id_election))

    gs          = Grade.objects.filter(election=election)
    return render(request, 'vote/vote.html', {'form': form,
                                            'grades': gs})



def set_voter(request):
    """
    View for updating voter profile (referred as user profile)
    """
    form = UserForm(request.POST or None)

    #TODO


def results(request, pk):
    election = get_object_or_404(Election, pk=pk)

    if election.state != Election.OVER:
        render(request, 'error.html', {'message':"L'élection n'est pas terminée"})


    # read database
    grades  = [g.name for g in Grade.objects.filter(election=election)]
    ratings = get_ratings(election)
    results = []
    cs      = Candidate.objects.filter(election=election)
    Nvotes  = len(Rating.objects.filter(election=election))

    if not Nvotes:
        render(request, 'error.html', {'message':"Aucun vote n'a été trouvé"})

    for i in range(len(cs)):
        result = Result(candidate=cs[i],
                        ratings=ratings[i, :],
                        grades=grades)
        results.append(result)

    # ranking according to the majority judgment
    ranking = [r.candidate for r in majority_judgment(results)]

    params = {'ranking':ranking, "nvotes":Nvotes, "id_election":pk}
    return render(request, 'vote/results.html', params)
