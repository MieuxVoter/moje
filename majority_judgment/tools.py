import numpy as np
from vote.models import *
from django.db.models import Count


def tie_breaking(A, B):
    ''' Algorithm to divide out candidates with the same median grade'''
    Ac   = np.copy(A)
    Bc   = np.copy(B)
    medA = arg_median(Ac)
    medB = arg_median(Bc)
    while medA == medB:
        Ac[medA] -= 1
        Bc[medB] -= 1
        if Ac[medA] < 0:
            return True
        if Bc[medB] < 0:
            return False
        medA = arg_median(Ac)
        medB = arg_median(Bc)
    return medA < medB

def majority_judgment(results):
    ''' Return the ranking from results using the majority judgment '''
    return sorted(results)

def arg_median(x):
    return np.argmin(np.abs(np.median(x) - x))

def sorted_scores(ratings, Ngrades):
    """ Compute the scores of each candidate """
    Nratings = len(ratings)
    grades   = range(Ngrades)
    scores   = [len(np.where(ratings == g)[0])/Nratings for g in grades]
    return scores


def plot_scores(scores, grades=[], names=[], height = 0.8, color = [], figure=None, output=True):
    """ scores is a 2D np.array """

    if not output:
        import matplotlib
        matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    Ncandidates, Ngrades = scores.shape
    # Ngrades     = len(grades)
    ind         = np.arange(Ncandidates)  # the x-axis locations for the novels
    plots       = []
    width_cumulative = np.zeros(Ncandidates)

    if color == []:
        color = [plt.cm.plasma(1-k/Ngrades, 1) for k in range(Ngrades)]
    if figure == None:
        figure = plt.figure()

    # Move the figure to the right
    ax = figure.add_subplot(111)
    pos1 = ax.get_position() # get the original position
    pos2 = [pos1.x0 + 0.1, pos1.y0,  pos1.width - 0.01, pos1.height]
    ax.set_position(pos2)

    # Draw horizontal bar
    for k in range(Ngrades):
        score = scores[:,k]
        p = plt.barh(ind, score, height=height, left=width_cumulative, color=color[k])
        width_cumulative += score
        plots.append(p)

    # Add labels, titles and legend
    plt.xlim((0, 1))
    plt.xlabel('Mentions')
    plt.ylabel('Candidats')
    plt.yticks(ind, names)
    plt.xticks([],[])
    plt.legend([p[0] for p in plots], grades, loc="best")


def get_scores(election):
    """ Compute a 2D array with all the ratings from the candidates
    FIXME: select only candidates from an election
    """
    scores = get_ratings(election)
    for i in range(len(scores)):
        scores[i] /= sum(scores[i])

    return scores


def get_ratings(election):
    """ Compute a 2D array with all the ratings from the candidates
    #FIXME this can largely be optimized
    """

    grades     = Grade.objects.filter(election=election)
    candidates = Candidate.objects.filter(election=election)
    scores     = np.zeros( (len(candidates), len(grades)) )

    # order in the grades is defined by their increasing id
    # could it be better?

    # order_grades = [grade.id for grade in grades]
    ratings    = Rating.objects.filter(election=election)

    for i in range(len(candidates)):
        for j in range(len(grades)):
            rating = ratings.filter(candidate=candidates[i], grade=grades[j])
            scores[i,j] = len(rating)

    return scores



class Result():
    """ Store a candidate with one's ratings """

    def __init__(self, name = "", ratings = np.array([]), scores = None, grades = [], candidate = None):

        self.name      = name
        self.ratings   = ratings
        self.grades    = grades
        self.scores    = scores
        self.candidate = candidate

        if name == "" and candidate is not None:
            self.name = candidate.user.first_name.title() + " " + candidate.user.last_name.title()
        if not ratings.size and scores is None:
            self.scores    = sorted_scores(ratings, len(grades))


    def __lt__(self, other):
        return tie_breaking(self.ratings, other.ratings)

    def __repr__(self):
        return str(self.name)

    def __str__(self):
        return str(self.name)
