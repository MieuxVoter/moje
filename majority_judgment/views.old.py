from django.shortcuts import render
from django.http import HttpResponseRedirect

# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
# from matplotlib.figure import Figure

import matplotlib as pl
pl.use('Agg')
import matplotlib.pyplot as plt


# from majority_judgment.tools import *
# from vote.models import Grade

def chart_results(request):
    # # read database
    # grades  = Grade.objects.all()
    # scores  = get_scores()
    #
    # # create figure
    # fig     = Figure()
    # plot_scores(scores, grades=grades, figure=fig)
    # canvas   = FigureCanvas(fig)
    #
    # # display figure
    # response = HttpResponse(content_type='image/png')
    # canvas.print_png(response)

    x = np.arange(0, 2 * np.pi, 0.01)
    s = np.cos(x) ** 2
    plt.plot(x, s)

    plt.xlabel('xlabel(X)')
    plt.ylabel('ylabel(Y)')
    plt.title('Simple Graph!')
    plt.grid(True)

    response = HttpResponse(content_type="image/jpeg")
    plt.savefig(response, format="png")

    return response
