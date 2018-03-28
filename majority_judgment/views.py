from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse

import matplotlib as pl
pl.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import os

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
    plt.savefig("static/img/results.png", format="png", frameon=False, transparent=True )
    
    response = HttpResponse(content_type='image/png') 
    Image.init()
    i = Image.open('static/img/results.png')
    i.save(response,'PNG')
    return response
     
