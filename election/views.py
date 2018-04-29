from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import DeleteView, CreateView
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.db import IntegrityError
from django.utils import timezone
from django.core.validators import validate_email

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

    try:
        election = find_election(election_id, check_user=request.user)
    except (Election.DoesNotExist, PermissionDenied) as e:
        return render(request, "error.html", {"error":"L'élection n'existe pas."})

    # manage form
    initial = { "name":  election.name,
                "note":  election.note,
                "start": election.start,
                "end":   election.end
                }
    disabled = election.state != Election.DRAFT
    form = GeneralStepForm(request.POST or None,
                           initial=initial,
                           disabled=disabled)

    if form.is_valid():
        # start = form.cleaned_data['start']
        # end   = form.cleaned_data['end']
        name  = form.cleaned_data['name']
        note  = form.cleaned_data['note']

        # record the election
        # election.start  = start
        # election.end    = end
        election.name   = name
        election.note   = note
        election.save()

        return HttpResponseRedirect('/election/manage/candidates/{:d}/'.format(election.pk))

    params =   {'form': form,
                "election_id": election.pk,
                "election": election,
                'grades':Grade.objects.filter(election=election),
                "state":  election.state,
                "supervisor": election.supervisor,
                "disabled": disabled
                }

    return render(request, 'election/manage_general.html', params)


@login_required
def launch_election(request, pk=-1):

    form = ConfirmStepForm(request.POST)
    if form.is_valid():
        return HttpResponseRedirect("/election/success/{:d}".format(pk))

    election = find_election(pk, check_user=request.user)
    params = {"supervisor": election.supervisor,
              "election": election,
              "form":form}

    return render(request, 'election/start.html', params)


@login_required
def confirm_launch_election(request, pk=-1):
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
    # if election.start < timezone.now().date():
    #     return render(request, 'election/error.html', {
    #         "election": election,
    #         "error": "Le début de l'élection est déjà passé."})
    # if election.end < timezone.now().date():
    #     return render(request, 'election/error.html', {
    #         "election": election,
    #         "error": "La fin de l'élection est déjà passée."})

    for v in voters:
        send_invite(v)

    election.state = Election.START
    election.save()

    params={'supervisor':election.supervisor,
            "election":election}

    return render(request, 'election/success_start.html', params)


def close_election(request, pk=-1):
    election = find_election(pk, check_user=request.user)
    election.state = Election.OVER
    election.save()

    return render(request, 'election/closed.html', {'supervisor':election.supervisor, 'election':election})


@login_required
def candidates_step(request, election_id=-1):
    """
    Manage candidates pool in the election
    """

    # find election given its id or create a new one
    election = find_election(election_id, check_user=request.user)

    candidates = Candidate.objects.filter(election=election)
    form = CreateCandidateForm()
    params = {
                "candidates": candidates,
                "election": election,
                "supervisor": election.supervisor,
                "form": form
            }

    return render(request, 'election/manage_candidates.html', params)



@login_required
def dashboard(request):
    supervisor  = Supervisor.objects.get_or_create(user=request.user)[0]
    elections   = Election.objects.filter(supervisor=supervisor) 
                    # .annotate(num_voters=Count('answer')) )
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

    try:
        first_name = request.GET.get('first_name', "")
        last_name = request.GET.get('last_name', "")
        program = request.GET.get('program', "")
        election_id = int(request.GET.get('election_id', -1))
        election = Election.objects.get(pk=election_id)
        username = "{}_{}_{:d}".format(first_name, last_name, election_id)
        print(username)
        user = User.objects.create(last_name=last_name, username=username)
    except ValueError:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)
    except Election.DoesNotExist:
        data = {'election': False,
                'error': "L'élection n'existe pas."
                }
        return JsonResponse(data)
    except IntegrityError as e:
        data = {'user':      False,
                'error':     "Le nom est déjà pris."
                }
        return JsonResponse(data)

    if not election.supervisor or election.supervisor.user != request.user:
        data = {'election':      False,
                'error': "Vous n'avez pas le droit de modifier cette élection."
                }
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'election':      False,
                'error': "L'élection a déjà commencée."
                }
        return JsonResponse(data)

    c = Candidate.objects.create(program=program, election=election, user=user)

    data = {
        'success': True,
        'id_candidate':c.pk,
        'id_candidate_user':c.user.pk
    }
    return JsonResponse(data)



class CandidateDelete(UserPassesTestMixin, DeleteView):
    """
    delete a candidate from a link
    #TODO do it from ajax request

    for the success_url, see https://docs.djangoproject.com/en/2.0/ref/class-based-views/mixins-editing/#django.views.generic.edit.DeletionMixin.success_url
    """

    model = Candidate
    success_url = "/election/manage/candidates/{election_id}/"

    # Delete without confirmation
    # It is not good practice : https://stackoverflow.com/questions/17475324/django-deleteview-without-confirmation-template
    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


    def delete(self, request, *args, **kwargs):
        """ Delete also the user if no account is related to it """
        success_url = self.get_success_url()

        # check if election is still in DRAFT
        if self.object.election.state != Election.DRAFT:
            return HttpResponseRedirect(success_url)

        user = self.object.user
        self.object.delete()

        if not Candidate.objects.filter(user=user).exists() and \
             not Voter.objects.filter(user=user).exists() and \
             not Supervisor.objects.filter(user=user).exists():
            user.delete()

        return HttpResponseRedirect(success_url)

    def test_func(self):
        candidate_id = self.kwargs['pk']
        self.object = get_object_or_404(Candidate, pk=candidate_id)
        supervisor = self.object.election.supervisor
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
    """
    print("foo")
    try:
        first_name = request.GET.get('first_name', "")
        last_name = request.GET.get('last_name', "")
        email = request.GET.get('email', "")
        election_id = int(request.GET.get('election_id', -1))
        validate_email(email)
        election = Election.objects.get(pk=election_id)
    except ValueError:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)
    except forms.ValidationError:
        data = {'election':      False,
                'error':         'Email address is not valid.'
                }
        return JsonResponse(data)
    except Election.DoesNotExist:
        data = {'election': False,
                'error': "L'élection n'existe pas."
                }
        return JsonResponse(data)

    if not election.supervisor or election.supervisor.user != request.user:
        data = {'election':      False,
                'error': "Vous n'avez pas le droit de modifier cette élection."
                }
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'election':      False,
                'error': "L'élection a déjà commencée."
                }
        return JsonResponse(data)

    username = "{}_{:d}".format(email, election_id)
    user, _ = User.objects.get_or_create(email=email,
                                         defaults={'last_name': last_name,
                                                   'first_name': first_name,
                                                   'username': username})
    voter, created = Voter.objects.get_or_create(election=election, user=user)

    if not created:
        data = {'election': False,
                'error': "L'électeur a déjà été ajouté."
                }
        return JsonResponse(data)

    data = {
        'success': True,
        'id_voter':voter.pk
    }

    return JsonResponse(data)



class VoterDelete(UserPassesTestMixin, DeleteView):
    """
    delete a voter to this election
    """
    model = Voter
    success_url = "/election/manage/voters/{election_id}/"


    def delete(self, request, *args, **kwargs):
        """ Delete also the user if no account is related to it """
        success_url = self.get_success_url()

        # check if election is still in DRAFT
        if self.object.election.state != Election.DRAFT:
            return HttpResponseRedirect(success_url)

        user = self.object.user
        self.object.delete()

        if not Candidate.objects.filter(user=user).exists() and \
             not Voter.objects.filter(user=user).exists() and \
             not Supervisor.objects.filter(user=user).exists():
            user.delete()

        return HttpResponseRedirect(success_url)


    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


    def test_func(self):
        """ ensure the user is allowed to delete this voter. """
        id_voter = self.kwargs['pk']
        self.object = get_object_or_404(Voter, pk=id_voter)
        supervisor = self.object.election.supervisor
        return supervisor and self.request.user == supervisor.user



# ================
# Grade management
# ================

@login_required
def create_grade(request):
    """
    Ajax request to create a grade
    """

    try:
        name = request.GET.get('name', "")
        code = name.upper()[:3]
        election_id = int(request.GET.get('election_id', -1))
        election = Election.objects.get(pk=election_id)
    except ValueError:
        data = {'election':      False,
                'error':         'Election id is not valid.'
                }
        return JsonResponse(data)
    except Election.DoesNotExist:
        data = {'election': False,
                'error': "L'élection n'existe pas."
                }
        return JsonResponse(data)

    if not election.supervisor or election.supervisor.user != request.user:
        data = {'election':      False,
                'error': "Vous n'avez pas le droit de modifier cette élection."
                }
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'election':      False,
                'error': "L'élection a déjà commencée."
                }
        return JsonResponse(data)

    grade = Grade.objects.create(name=name, code=code, election=election)

    data = {
        'success': True,
        'id_grade': grade.pk
    }

    return JsonResponse(data)



class GradeDelete(UserPassesTestMixin, DeleteView):
    """
    delete a grade to this election
    """
    model = Grade
    success_url = "/election/manage/general/{election_id}/"


    def delete(self, request, *args, **kwargs):
        # check if election is still in DRAFT
        if self.object.election.state != Election.DRAFT:
            return HttpResponseRedirect(success_url)

        return super(GradeDelete, self).delete(request, *args, **kwargs)



    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


    def test_func(self):
        """ ensure the user is allowed to delete this grade. """
        id_grade = self.kwargs['pk']
        self.object = get_object_or_404(Grade, pk=id_grade)
        supervisor = self.object.election.supervisor
        return supervisor and self.request.user == supervisor.user
