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
    # read database
    grades  = [g.name for g in Grade.objects.all()]
    ratings = get_ratings()
    results = []
    cs      = Candidate.objects.all()
    Nvotes  = len(Rating.objects.all())

    for i in range(len(cs)):
        result = Result(candidate = cs[i], ratings = ratings[i, :], grades = grades)
        results.append(result)

    # ranking according to the majority judgment
    ranking = [r.candidate for r in majority_judgment(results)]

    return render(request, 'vote/results.html', {'ranking':ranking, "nvotes":Nvotes})
