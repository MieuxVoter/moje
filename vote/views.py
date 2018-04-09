from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import available_attrs, method_decorator

from vote.models import *
from vote.forms import *
from vote.tools import *
from majority_judgment.tools import *


## TODO: grant access only the election of the voter

class CandidateList(LoginRequiredMixin, generic.ListView):
    model = Candidate

    def get_queryset(self):
        election = Election.objects.get(pk=self.kwargs['id_election'])
        return Candidate.objects.filter(election=election)

class CandidateDetail(LoginRequiredMixin, generic.DetailView):
    model = Candidate




@login_required
def voter_detail(request, pk):
    user = User.objects.get(pk=pk)
    voter =  Voter.objects.filter(user=user)
    return render(request, 'vote/voter_detail.html', {"voter":voter})


@login_required
def redirect_vote(request):
    try:
        voter       = Voter.objects.get(user=request.user)
        id_election = voter.election.pk
        return HttpResponseRedirect('/vote/{:d}/'.format(id_election))
    except Voter.DoesNotExist:
        return render(request, 'error.html', {"message":"Nous n'avons pas trouvé d'élections pour vous..."})


@login_required
def redirect_results(request):
    try:
        voter       = Voter.objects.get(user=request.user)
        id_election = voter.election.pk
        return HttpResponseRedirect('/results/{:d}/'.format(id_election))
    except Voter.DoesNotExist:
        return render(request, 'error.html', {"message":"Nous n'avons pas trouvé d'élections pour vous..."})




@login_required
def redirect_candidates(request):
    try:
        voter       = Voter.objects.get(user=request.user)
        id_election = voter.election.pk
        return HttpResponseRedirect('/candidates/{:d}/'.format(id_election))
    except Voter.DoesNotExist:
        return render(request, 'error.html', {"message":"Nous n'avons pas trouvé d'élections pour vous..."})



@login_required
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
        return HttpResponseRedirect('/results/{:d}/'.format(id_election))

    gs          = Grade.objects.filter(election=election)
    return render(request, 'vote/vote.html', {'form': form,
                                            'grades': gs})




@login_required
def set_voter(request):
    """
    View for updating voter profile (referred as user profile)
    """
    form = UserForm(request.POST or None)

    #TODO


@login_required
def results(request, id_election):
    election = get_object_or_404(Election, pk=id_election)

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

    params = {'ranking':ranking, "nvotes":Nvotes, "id_election":id_election}
    return render(request, 'vote/results.html', params)
