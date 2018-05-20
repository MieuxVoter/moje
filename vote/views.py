from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import available_attrs, method_decorator
from django.utils.translation import gettext_lazy as _

from vote.models import *
from vote.forms import *
from vote.tools import *
from majority_judgment.tools import *



@login_required
def redirect_vote(request):
    try:
        voter = Voter.objects.filter(user=request.user).first()
        election_id = voter.election.pk
        return HttpResponseRedirect('/vote/{:d}/'.format(election_id))
    except Voter.DoesNotExist:
        return render(request, 'vote/error.html', {"error":_("No election has been found for you...")})


@login_required
def vote(request, election_id):
    try:
        election = Election.objects.get(pk=election_id)
        voter = Voter.objects.get(election=election, user=request.user)
    except Election.DoesNotExist:
        return render(request, 'vote/error.html', {"error":_("The election does not exist.")})
    except Voter.DoesNotExist:
        return render(request, 'vote/error.html', {"error":"You are not registered to this election!", "election":election})

    if election.state == Election.OVER:
        return render(request, 'vote/error.html',
            {"error":"The election is over.", "election":election})
    elif election.state == Election.DRAFT:
        return render(request, 'vote/error.html',
            {"error":"The election has not started yet.", "election":election})

    form = VoteForm(request.POST or None, election=election)
    if form.is_valid():
        # check whether the voter has already casted a vote
        if Rating.objects.filter(voter=voter, election=election).exists():
            return render(request, 'vote/error.html',
                {"error":"You can vote only once.", "election":election})

        for c, g in form_grades(form, election).items():
            r = Rating(candidate=c, grade=g, voter=voter, election=election)
            r.save()

        return HttpResponseRedirect('/vote/success/{}'.format(election_id))

    params = {'form': form,
              'election': election,
              'grades': Grade.objects.filter(election=election),
              'voter': voter }
    return render(request, 'vote/vote.html', params)



@login_required
def success(request, pk):
    try:
        election = Election.objects.get(pk=pk)
        voter = Voter.objects.get(election=election, user=request.user)
    except Election.DoesNotExist:
        return render(request, 'vote/error.html', {"error":"The election does not exist.", "election":election})
    except Voter.DoesNotExist:
        return render(request, 'vote/error.html', {"error":"You are not registered to this election!", "election":election})
    params = {'election': election,
              'voter': voter }
    return render(request, 'vote/success.html', params)
