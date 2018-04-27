from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import DeleteView, CreateView
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.db import IntegrityError

from datetime import datetime

from vote.models import *
from election.forms import *
from election.tools import *
from utils.mixins import SupervisorTestMixin, SupervisorFetchMixin



@login_required
def create_election(request):
    supervisor = Supervisor.objects.get_or_create(user=request.user)[0]
    election   = Election.objects.create(supervisor=supervisor)

    # default grades
    Grade.objects.create(name="Très bien",  election=election, code="tb")
    Grade.objects.create(name="Bien",       election=election, code="b")
    Grade.objects.create(name="Passable",   election=election, code="p")
    Grade.objects.create(name="Insuffisant",election=election, code="ins")
    Grade.objects.create(name="À rejeter",  election=election, code="rej")

    return HttpResponseRedirect('/election/manage/general/{:d}/'.format(election.pk))


@login_required
def general_step(request, election_id=-1):
    """
    General parameters of an election.
    """

    election = find_election(election_id, check_user=request.user)

    # manage form
    initial = { "name":  election.name,
                "note":  election.note,
                "start": election.start,
                "end":   election.end,
                # "state": election.state
                }

    form = GeneralStepForm(request.POST or None, initial=initial)
    if form.is_valid():
        start = form.cleaned_data['start']
        end   = form.cleaned_data['end']
        name  = form.cleaned_data['name']
        note  = form.cleaned_data['note']

        # record the election
        election.start  = end
        election.end    = end
        election.name   = name
        election.note   = note
        election.save()

        return HttpResponseRedirect('/election/manage/general/{:d}/'.format(election.pk))

    params =   {'form': form,
                "election_id": election.pk,
                "election": election,
                'grades':Grade.objects.filter(election=election),
                "state":  election.state,
                "supervisor": election.supervisor
                }

    return render(request, 'election/manage_general.html', params)


@login_required
def launch_election(request, pk=-1):
    """
    Launch an election: send mail to all voters and change the state of the election
    """

    election    = find_election(pk, check_user=request.user)
    voters      = Voter.objects.filter(election=election)
    Ncandidates = Candidate.objects.filter(election=election).count()
    Nvoters     = voters.count()

    if election.state != Election.DRAFT:
        return render(request, 'election/error.html', {
            "election": election,
            "error": "L'élection a déjà commencée."})
    if Nvoters == 0:
        return render(request, 'election/error.html', {
            "election": election,
            "error": "Il n'y pas d'électeurs."})
    if Ncandidates == 0:
        return render(request, 'election/error.html', {
            "election": election,
            "error": "Il n'y pas de candidats."})
    if election.name == "":
        return render(request, 'election/error.html', {
            "election": election,
            "error": "L'élection n'a pas de nom."})
    if election.start < datetime.now().date():
        return render(request, 'election/error.html', {
            "election": election,
            "error": "Le début de l'élection est déjà passé."})
    if election.end < datetime.now().date():
        return render(request, 'election/error.html', {
            "election": election,
            "error": "La fin de l'élection est déjà passée."})

    for v in voters:
        send_invite(v)

    election.state = Election.START
    election.save()

    params={'supervisor':election.supervisor,
            "election":election}

    return render(request, 'election/start.html', params)


def close_election(request, pk=-1):
    election = find_election(election_id, check_user=request.user)
    election.state = Election.OVER
    election.save()

    return render(request, 'election/closed.html', params={'supervisor':election.supervisor,'election':election})


@login_required
def candidates_step(request, election_id=-1):
    """
    Manage candidates pool in the election
    """

    # find election given its id or create a new one
    election = find_election(election_id, check_user=request.user)

    candidates = Candidate.objects.filter(election=election)

    params = {
                "candidates": candidates,
                "election": election,
                "supervisor": election.supervisor
            }

    return render(request, 'election/manage_candidates.html', params)



@login_required
def dashboard(request):
    supervisor  = Supervisor.objects.get_or_create(user=request.user)[0]
    elections   = Election.objects.filter(supervisor=supervisor)
    #FIXME annotate user_voters with has_voted and ended
    user_voters = Voter.objects.filter(user=request.user)
    return render(request, 'election/dashboard.html',
                    {'election_list': elections,
                     'user_voters': user_voters})


@login_required
def election_detail(request, election_id):
    template_name = "election/election_detail.html"
    supervisor    = None
    voter         = None

    try:
        election = Election.objects.get(pk=election_id)
        if election.supervisor and election.supervisor.user == request.user:
            supervisor = election.supervisor
        else:
            voter = Voter.objects.get(election=election, user=request.user)

    except Election.DoesNotExist:
        return render(request, 'election/error.html',
                        {"election": election,
                         "error":"L'élection demandée n'existe pas."})
    except Voter.DoesNotExist:
        return render(request, 'election/error.html',
                {"election": election,
                "error":"Vous n'avez pas les droits d'accès à cette élection."})

    params = {"voter": voter,
              "election": election,
              "supervisor": supervisor,
              'election_id':election_id}

    return render(request, template_name, params)



@login_required
def redirect_election(request):
    try:
        voter       = Voter.objects.get(user=request.user)
        election_id = voter.election.pk
        return HttpResponseRedirect('/election/{:d}/'.format(election_id))
    except Voter.DoesNotExist:
        return render(request, 'election/error.html', {
                    "election": election,
                    "error":"Nous n'avons pas trouvé d'élections pour vous..."})


class ElectionList(LoginRequiredMixin, SupervisorFetchMixin, generic.ListView):
    template_name   = "election/dashboard.html"

    def get_queryset(self):
        self.supervisor      = Supervisor.objects.get_or_create(user=self.request.user)[0]
        elections       = Election.objects.filter(supervisor=self.supervisor)
        queryset        = elections.annotate(num_voters=Count('voter'),
                                        num_candidates=Count('candidate'))
        return queryset


class ElectionDelete(SupervisorTestMixin, DeleteView):

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
    """


    name        = request.GET.get('name')
    program     = request.GET.get('program')
    election_id = request.GET.get('election_id', -1)
    if not election_id:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)

    election_id = int(election_id)
    username    = "{}_{:d}".format(name, election_id)
    election = find_election(election_id, check_user=request.user)
    if not election:
        data = {'election':      False,
                'error':         'Election does not seem to exist.'
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

    c = Candidate(program=program, election=election, user=user)
    c.save()

    data = {
        'success': True,
        'id_candidate':c.pk
    }
    return JsonResponse(data)



class CandidateDelete(UserPassesTestMixin, DeleteView):
    """
    delete a candidate from ajax request
    """
    model       = Candidate
    success_url = "/election/manage/candidates/{election_id}/"

    # Delete the confirmation
    # It is not good practice : https://stackoverflow.com/questions/17475324/django-deleteview-without-confirmation-template
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def test_func(self):
        id_candidate    = self.kwargs['pk']
        candidate       = get_object_or_404(Candidate, pk=id_candidate)
        supervisor      = candidate.election.supervisor
        return supervisor and self.request.user == supervisor.user




# ================
## Managing voters
# ================
@login_required
def voters_step(request, election_id=-1):
    """
    Manage voters pool in the election
    """

    election = find_election(election_id)
    if not election:
        return HttpResponseRedirect('/election/manage/general/')

    voters = Voter.objects.filter(election=election)

    params = {
                "election": election,
                "election_id": election_id,
                "voters":  voters,
                "supervisor": election.supervisor
            }

    return render(request, 'election/manage_voters.html', params)


@login_required
def create_voter(request):
    """
    Ajax request to create a voter

    #TODO catch is voter already exist
    """


    first_name    = request.GET.get('first_name', "")
    last_name     = request.GET.get('last_name', "")
    email         = request.GET.get('email', "")
    election_id   = int(request.GET.get('election_id', -1))
    username      = "{}_{}_{:d}".format(first_name,last_name, election_id)

    election = find_election(election_id, check_user=request.user)
    if not election or election_id < 0:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)


    user = User.objects.create( last_name=last_name,
                        first_name=first_name,
                        username=username,
                        email=email
                      )
    v   = Voter.objects.create(election=election, user=user)

    data = {
        'success': True,
        'id_voter':v.pk
    }

    return JsonResponse(data)



class VoterDelete(UserPassesTestMixin, DeleteView):
    """
    delete a voter to this election
    """
    model       = Voter
    success_url = "/election/manage/voters/{election_id}/"

    # Delete the confirmation
    # It is not good practice : https://stackoverflow.com/questions/17475324/django-deleteview-without-confirmation-template
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    # ensure the user is allowed to delete this voter
    def test_func(self):
        id_candidate    = self.kwargs['pk']
        candidate       = get_object_or_404(Candidate, pk=id_candidate)
        supervisor      = candidate.election.supervisor
        return supervisor and self.request.user == supervisor.user
