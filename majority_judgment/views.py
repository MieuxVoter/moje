from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse

import matplotlib as pl
pl.use('Agg')
import matplotlib.pyplot as plt

from majority_judgment.tools import *
from vote.models import Grade

def chart_results(request):
    # read database
    grades  = [g.name for g in Grade.objects.all()]
    scores  = get_scores()
    names   = []
    for c in Candidate.objects.all():
        name = c.user.first_name.title() + " " + c.user.last_name.title()
        names.append(name)

    # display figure
    plot_scores(scores, grades=grades,  names=names, output=False)
    response = HttpResponse(content_type="image/jpeg")
    plt.savefig(response, format="png")

    return response
