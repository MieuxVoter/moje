from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import DeleteView, CreateView
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db import IntegrityError

from vote.models import *
from election.forms import *
from election.tools import *



@login_required
def create_election(request):
    election = Election()
    election.save()

    # default grades
    Grade(name="Très bien", election=election, code="tb").save()
    Grade(name="Bien", election=election, code="b").save()
    Grade(name="Passable", election=election, code="p").save()
    Grade(name="Insuffisant", election=election, code="ins").save()
    Grade(name="À rejeter", election=election, code="rej").save()
    grades = Grade.objects.filter(election=election)

    return HttpResponseRedirect('/election/manage/general/{:d}/'.format(election.pk))


@login_required
def general_step(request, id_election=-1):
    """
    General parameters of an election.
    """
    print(id_election)
    election = find_election(id_election)

    # manage form
    initial = { "name":  election.name,
                # "note":  election.note,
                "start": election.start,
                "end":   election.end,
                # "state": election.state
                }

    form = GeneralStepForm(request.POST or None, initial=initial)
    if form.is_valid():
        # FIXME: use the real voter
        voter = Voter.objects.first()

        start = form.cleaned_data['start']
        end   = form.cleaned_data['end']
        name  = form.cleaned_data['name']
        # note  = form.cleaned_data['note']

        # record the election
        election.voter  = voter
        election.start  = end
        election.end    = end
        election.name   = name
        # election.note   = note
        election.save()

        return HttpResponseRedirect('/election/manage/general/{:d}/'.format(election.pk))

    params =   {'form': form,
                "id_election": election.pk,
                'grades':Grade.objects.filter(election=election),
                "state":  election.state,

                }

    return render(request, 'election/manage_general.html', params)

# def config_step(request, id_election=-1):
#     """
#     Configuration step on the voting system in an election.
#     """
#
#     # find election given its id or create a new one
#     election = find_election(id_election)
#     if not election:
#         return HttpResponseRedirect('/election/manage/general/')
#
#     # TODO modify grades in JM
#     # TODO select JM or VM
#     # FIXME this is only done with default grades
#
#     grades = Grade.objects.filter(election=election)
#
#     if not grades:
#         Grade(name="Très bien", election=election, code="tb").save()
#         Grade(name="Bien", election=election, code="b").save()
#         Grade(name="Passable", election=election, code="p").save()
#         Grade(name="Insuffisant", election=election, code="ins").save()
#         Grade(name="À rejeter", election=election, code="rej").save()
#         grades = Grade.objects.filter(election=election)
#
#
#     params = {
#
#                 "id_election":  id_election,
#                 "grades":      grades
#             }
#
#     return render(request, 'election/manage_config.html', params)

@login_required
def launch_election(request, pk=-1):
    """
    Launch an election: send mail to all voters and change the state of the election
    """

    election = find_election(pk)

    voters = Voter.objects.filter(election=election)
    for v in voters:
        send_invite(v)

    election.state = Election.START
    election.save()
    return render(request, 'election/start.html')


def close_election(request, pk=-1):
    election = find_election(pk)
    election.state = Election.OVER
    election.save()
    return render(request, 'election/closed.html')

@login_required
def candidates_step(request, id_election=-1):
    """
    Manage candidates pool in the election
    """

    # find election given its id or create a new one
    election = find_election(id_election)
    if not election:
        return HttpResponseRedirect('/election/manage/general/')

    candidates = Candidate.objects.filter(election=election)

    params = {

                "id_election": id_election,
                "candidates": candidates
            }

    return render(request, 'election/manage_candidates.html', params)



@login_required
def dashboard(request):
    # FIXME: use the real voter
    voter       = Voter.objects.first()
    elections   = Election.objects.all()
    return render(request, 'election/dashboard.html', {'elections':elections})


class ElectionDetail(LoginRequiredMixin, generic.DetailView):
    model = Election

class ElectionList(LoginRequiredMixin, generic.ListView):
    model           = Election
    template_name   = "election/dashboard.html"
    queryset        = Election.objects.annotate(num_voters=Count('voter'),
                                                num_candidates=Count('candidate'))

class ElectionDelete(LoginRequiredMixin, DeleteView):
    """
    #FIXME check whether user is allowed to delete this election
    """
    model       = Election
    success_url = "/election/dashboard/"

    # Delete the confirmation
    # It is not good practice : https://stackoverflow.com/questions/17475324/django-deleteview-without-confirmation-template
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)



@login_required
def create_candidate(request):
    """
    Ajax request to create a candidate

    #TODO it would be better with a `FormView <https://docs.djangoproject.com/en/2.0/ref/class-based-views/generic-editing/#django.views.generic.edit.FormView>`_.
    + `ajax request <https://stackoverflow.com/questions/8059160/django-apps-using-class-based-views-and-ajax>`_.

    https://stackoverflow.com/questions/10382838/how-to-set-foreignkey-in-createview

    #FIXME check whether user is allowed to create a candidate to this election
    """


    name        = request.GET.get('name', "")
    bio         = request.GET.get('bio', "")
    id_election = int(request.GET.get('id_election', -1))
    username    = "{}_{:d}".format(name, id_election)

    # FIXME check whether the id_election belongs to the user
    election = find_election(id_election)
    if not election or id_election < 0:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)

    try:
        user = User(last_name=name, username=username)
        user.save()
    except IntegrityError as e:
        data = {'user':      False,
                'error':     "The user name is already taken."
                }
        return JsonResponse(data)

    c = Candidate(bio=bio, election=election, user=user)
    c.save()

    data = {
        'success': True,
        'id_candidate':c.pk
    }
    return JsonResponse(data)



class CandidateDelete(LoginRequiredMixin, DeleteView):
    """
    #FIXME check whether user is allowed to delete a candidate to this election
    """
    model       = Candidate
    success_url = "/election/manage/candidates/{election_id}/"

    # Delete the confirmation
    # It is not good practice : https://stackoverflow.com/questions/17475324/django-deleteview-without-confirmation-template
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)




# ================
## Managing voters
# ================
@login_required
def voters_step(request, id_election=-1):
    """
    Manage voters pool in the election
    """

    election = find_election(id_election)
    if not election:
        return HttpResponseRedirect('/election/manage/general/')

    voters = Voter.objects.filter(election=election)

    params = {

                "id_election": id_election,
                "voters":  voters
            }

    return render(request, 'election/manage_voters.html', params)


@login_required
def create_voter(request):
    """
    Ajax request to create a voter

    #FIXME check whether user is allowed to create a voter to this election

    #TODO catch is voter already exist
    """


    first_name    = request.GET.get('first_name', "")
    last_name     = request.GET.get('last_name', "")
    email         = request.GET.get('email', "")
    id_election   = int(request.GET.get('id_election', -1))
    username      = "{}_{}_{:d}".format(first_name,last_name, id_election)

    # FIXME check whether the id_election belongs to the user
    election = find_election(id_election)
    if not election or id_election < 0:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)


    user = User(last_name=last_name, first_name=first_name, username=username, email=email)
    user.save()
    v = Voter(election=election, user=user)
    v.save()

    data = {
        'success': True,
        'id_voter':v.pk
    }

    return JsonResponse(data)



class VoterDelete(LoginRequiredMixin, DeleteView):
    """
    #FIXME check whether user is allowed to delete a voter to this election
    """
    model       = Voter
    success_url = "/election/manage/voters/{election_id}/"

    # Delete the confirmation
    # It is not good practice : https://stackoverflow.com/questions/17475324/django-deleteview-without-confirmation-template
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)
