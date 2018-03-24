from django.shortcuts import render
from django.views import generic
from django.http import HttpResponseRedirect

from vote.models import *
from vote.forms import VoteForm, form_grades
from majority_judgment.tools import *


class CandidateList(generic.ListView):
    model = Candidate

class CandidateDetail(generic.DetailView):
    model = Candidate



def vote(request):
    form = VoteForm(request.POST or None)

    if form.is_valid():
        # FIXME: use the real voter
        voter = Voter.objects.first()

        # FIXME: check whether the voter has already casted a vote
        for c, g in form_grades(form).items():
            r = Rating(candidate=c, grade=g, voter=voter)
            r.save()
        return HttpResponseRedirect('/results/')

    gs = Grade.objects.all()
    return render(request, 'vote/vote.html', {'form': form,
                                            'grades': gs})


def results(request):
    vote    = request.POST
    ranking = majority_judgment(vote)
    return render(request, 'vote/results.html', {'ranking':ranking})
