from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse

import matplotlib as pl
pl.use('Agg')
import matplotlib.pyplot as plt
import os

from majority_judgment.tools import *
from vote.models import Grade, Election


from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import io

def chart_results(request, election_id):
    # read database
    election = get_object_or_404(Election, pk=election_id)
    grades  = [g.name for g in Grade.objects.filter(election=election)]
    scores  = get_scores(election)
    names   = []
    for c in Candidate.objects.filter(election=election):
        name = c.user.first_name.title() + " " + c.user.last_name.title()
        names.append(name)

    # display figure
    plot_scores(scores, grades=grades,  names=names, output=False)
    plt.savefig("static/img/results.png", format="png", frameon=False, transparent=True )
    f = Figure()
    canvas = FigureCanvasAgg(f)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(f)
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    return response
