from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import DeleteView, CreateView
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.db import IntegrityError
from django.utils import timezone
from django.utils.html import escape
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from vote.models import *
from election.forms import *
from election.tools import *
from moje.mixins import SupervisorTestMixin, SupervisorFetchMixin

try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape  # python 2.x


def create_election(request):
    election = Election.objects.create()
    if request.user.is_authenticated:
        supervisor = Supervisor.objects.create(user=request.user, election=election)

    # default grades
    Grade.objects.create(name=_("Excellent"),  election=election, code="exc")
    Grade.objects.create(name=_("Very good"),  election=election, code="tb")
    Grade.objects.create(name=_("Good"),       election=election, code="b")
    Grade.objects.create(name=_("Fair"),   election=election, code="p")
    Grade.objects.create(name=_("Poor"),election=election, code="ins")
    Grade.objects.create(name=_("To Reject"),  election=election, code="rej")

    return HttpResponseRedirect('/election/manage/general/{:d}/'.format(election.pk))


def general_step(request, election_id=-1):
    """
    General parameters of an election.
    """

    user = request.user if request.user.is_authenticated else None
    try:
        election = find_election(election_id, check_user=user)
    except (Election.DoesNotExist, PermissionDenied) as e:
        return render(request, "error.html", {"error":_("The election does not exist.")})

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
        name  = form.cleaned_data['name']
        note  = form.cleaned_data['note']

        # record the election
        election.name   = name
        election.note   = note
        election.save()

        return HttpResponseRedirect('/election/manage/candidates/{:d}/'.format(election.pk))

    supervisor = Supervisor.objects.get(election=election, user=user) if user is not None \
            else None
    params =   {'form': form,
                "election_id": election.pk,
                "election": election,
                'grades':Grade.objects.filter(election=election),
                "state":  election.state,
                "supervisor": supervisor,
                "disabled": disabled
                }

    return render(request, 'election/manage_general.html', params)


def launch_election(request, pk=-1):

    form = ConfirmStepForm(request.POST or None)
    if form.is_valid():
        return HttpResponseRedirect("/election/success/{:d}".format(pk))

    election = find_election(pk, check_user=request.user)
    supervisor = Supervisor.objects.get(election=election, user=request.user)
    params = {"supervisor": supervisor,
              "election": election,
              "form":form}

    return render(request, 'election/start.html', params)


def confirm_launch_election(request, pk=-1):
    """
    Launch an election: send mail to all voters and change the state of the election
    """

    user = request.user if request.user.is_authenticated else None
    election    = find_election(pk, check_user=user)
    voters      = Voter.objects.filter(election=election)
    Ncandidates = Candidate.objects.filter(election=election).count()
    Nvoters     = voters.count()

    if election.state != Election.DRAFT:
        return render(request, 'election/error.html', {
            "election": election,
            "error": _("The election has already begun")})
    if Nvoters == 0:
        return render(request, 'election/error.html', {
            "election": election,
            "error": _("There is not any voter")})
    if Ncandidates == 0:
        return render(request, 'election/error.html', {
            "election": election,
            "error": _("There is not any candidate")})
    if election.name == "":
        return render(request, 'election/error.html', {
            "election": election,
            "error": _("The election has not set up")})

    for v in voters:
        send_invite(v)

    election.state = Election.START
    election.save()
    supervisor = Supervisor.objects.get(election=election, user=user)
    params={'supervisor':supervisor,
            "election":election}

    return render(request, 'election/success_start.html', params)


@login_required
def close_election(request, pk=-1):
    election = find_election(pk, check_user=request.user)
    election.state = Election.OVER
    election.save()
    supervisor = Supervisor.objects.get(election=election, user=request.user)
    return render(request, 'election/closed.html', {'supervisor':supervisor, 'election':election})


def candidates_step(request, election_id=-1):
    """
    Manage candidates pool in the election
    """

    # find election given its id or create a new one
    user = request.user if request.user.is_authenticated else None
    election = find_election(election_id, check_user=user)
    supervisor = Supervisor.objects.get(election=election, user=user)
    candidates = Candidate.objects.filter(election=election)
    form = CreateCandidateForm()
    params = {
                "candidates": candidates,
                "election": election,
                "supervisor": supervisor,
                "form": form
            }

    return render(request, 'election/manage_candidates.html', params)



@login_required
def dashboard(request):
    user = request.user 
    supervisors = Supervisor.objects.filter(user=user)
    elections = Election.objects.filter(pk__in=supervisors.values('election_id'))

    if elections:
        elections.annotate(progress=Count('rating')/Count('voter')/Count('grade') )
    # supervisors  = Supervisor.objects.filter(election=election, user=request.user)[0]

    #TODO: this is not optimized at all
    user_voters = Voter.objects.filter(user=request.user)
    votes = [voter.election for voter in user_voters]
    for v in votes:
        progress = Rating.objects.filter(election=v).count() /    \
                     Voter.objects.filter(election=v).count() /     \
                     Candidate.objects.filter(election=v).count()
        v.progress = int(progress*100)
        v.has_voted = Rating.objects.filter(election=v,
                                            voter__in=user_voters)  \
                                     .exists()


    return render(request, 'election/dashboard.html',
                    {'election_list': elections,
                     'votes': votes})


@login_required
def election_detail(request, election_id):
    template_name = "election/election_detail.html"
    supervisor = None
    voter = None

    try:
        election = Election.objects.get(pk=election_id)
        if Supervisor.objects.filter(election=election, user=request.user):
            supervisor = supervisor
        else:
            voter = Voter.objects.get(election=election, user=request.user)

    except Election.DoesNotExist:
        return render(request, 'election/error.html',
                        {"election": election,
                         "error":_("The election does not exist")})
    except Voter.DoesNotExist:
        return render(request, 'election/error.html',
                {"election": election,
                "error":"You are not allowed to be here"})

    params = {"voter": voter,
              "election": election,
              "supervisor": supervisor,
              'election_id':election_id}

    return render(request, template_name, params)



def redirect_election(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/election/manage/general/')

    try:
        voter       = Voter.objects.get(user=request.user)
        election_id = voter.election.pk
        return HttpResponseRedirect('/election/{:d}/'.format(election_id))
    except Voter.DoesNotExist:
        return render(request, 'election/error.html', {
                    "election": election,
                    "error":"No election has been found for you..."})



class ElectionList(LoginRequiredMixin, generic.ListView):
    template_name   = "election/dashboard.html"

    def get_queryset(self):
        self.supervisors = Supervisor.objects.filter(user=self.request.user)
        elections   = Election.objects.filter(pk__in=self.supervisors.values('election_id'))
        queryset = elections.annotate(num_voters=Count('voter'),
                                      num_candidates=Count('candidate'))
        return queryset


class ElectionDelete(SupervisorTestMixin, DeleteView):

    model       = Election
    success_url = "/election/dashboard/"

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        voters = Voter.objects.filter(election=self.object)
        for voter in voters:
            user = voter.user
            user.delete()
        return super(DeleteView, self).post(*args, **kwargs)



def create_candidate(request):
    """
    Ajax request to create a candidate

    #TODO it would be better with a `FormView <https://docs.djangoproject.com/en/2.0/ref/class-based-views/generic-editing/#django.views.generic.edit.FormView>`_.
    + `ajax request <https://stackoverflow.com/questions/8059160/django-apps-using-class-based-views-and-ajax>`_.

    https://stackoverflow.com/questions/10382838/how-to-set-foreignkey-in-createview
    """

    user = request.user if request.user.is_authenticated else None

    try:
        label = request.GET.get('label', "")
        description = request.GET.get('description', "")
        election_id = int(request.GET.get('election_id', -1))
        election = Election.objects.get(pk=election_id)
    except ValueError:
        data = {'election':      False,
                'error':         _('Election id is not valid.')
                }
        return JsonResponse(data)
    except Election.DoesNotExist:
        data = {'election': False,
                'error': _("The election does not exist")
                }
        return JsonResponse(data)
    except IntegrityError as e:
        data = {'user':      False,
                'error':     _("The name has already been taken")
                }
        return JsonResponse(data)

    if not Supervisor.objects.filter(election=election, user=user).exists():
        data = {'election':      False,
                'error': _("You are not allowed to be here")
                }
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'election':      False,
                'error': _("The election has already begun")
                }
        return JsonResponse(data)

    c = Candidate.objects.create(label=label,
                                 description=description,
                                 election=election)

    data = {
        'success': True,
        'id_candidate':c.pk
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

        self.object.delete()

        return HttpResponseRedirect(success_url)

    def test_func(self):
        candidate_id = self.kwargs['pk']
        self.object = get_object_or_404(Candidate, pk=candidate_id)
        return Supervisor.objects.filter(election=self.object.election, user=self.request.user).exists()





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
    supervisor = Supervisor.objects.get(election=election, user=request.user)
    params = {
                "election": election,
                "election_id": election_id,
                "voters":  voters,
                "supervisor": supervisor
            }

    return render(request, 'election/manage_voters.html', params)


@login_required
def voters_list_step(request, election_id=-1):
    """
    Manage voters pool in the election with a textarea
    """

    election = find_election(election_id)
    if not election:
        return HttpResponseRedirect('/election/manage/general/')

    form = VotersListStepForm(request.POST or None)
    success = ""
    error = ""
    if form.is_valid():
        list  = form.cleaned_data['list']
        voters = list.split("\n")

        for detail in voters:
            try:
                details = detail.rstrip().split(", ")
                first_name = details[1].strip()
                last_name = details[0].strip()
                email = details[2].strip()
                validate_email(email)
                username = "{}_{:d}".format(email, election_id)
                defaults = {'last_name': last_name,
                            'first_name': first_name,
                            'username': username}
                user = User.objects.get_or_create(email=details[2],
                                                  defaults=defaults)[0]
                voter = Voter.objects.create(election=election, user=user)
                success += str(voter)
            except (ValidationError, IndexError) as e:
                error += _("Error to decode") + " " + escape(detail)

    voters = Voter.objects.filter(election=election)
    supervisor = Supervisor.objects.get(election=election, user=request.user)
    params = {
                "election": election,
                "election_id": election_id,
                "voters":  voters,
                "supervisor": supervisor,
                "form": form,
                "success": success,
                "error": error
            }

    return render(request, 'election/manage_list_voters.html', params)


@login_required
def create_voter(request):
    """
    Ajax request to create a voter
    """

    try:
        first_name = request.GET.get('first_name', "")
        last_name = request.GET.get('last_name', "")
        email = request.GET.get('email', "").rstrip()
        election_id = int(request.GET.get('election_id', -1))
        validate_email(email)
        election = Election.objects.get(pk=election_id)
    except ValueError:
        data = {'election':      False,
                'error':         _('Election id is not valid.')
                }
        return JsonResponse(data)
    except forms.ValidationError:
        data = {'election':      False,
                'error':        _('Email address is not valid.')
                }
        return JsonResponse(data)
    except Election.DoesNotExist:
        data = {'election': False,
                'error': _("The election does not exist")
                }
        return JsonResponse(data)

    if not Supervisor.objects.filter(election=election, user=request.user).exists():
        data = {'election':      False,
                'error': _("You are not allowed to be here")
                }
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'election':      False,
                'error': _("The election has already begun")
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
                'error': _("The voter has already been recorded")
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
        user.delete()

        return HttpResponseRedirect(success_url)


    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


    def test_func(self):
        """ ensure the user is allowed to delete this voter. """
        id_voter = self.kwargs['pk']
        self.object = get_object_or_404(Voter, pk=id_voter)
        supervisor = Supervisor.objects.filter(election=self.object.election, user=self.request.user)
        return supervisor.exists()



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
                'error':         _('Election id is not valid.')
                }
        return JsonResponse(data)
    except Election.DoesNotExist:
        data = {'election': False,
                'error': _("The election does not exist")
                }
        return JsonResponse(data)

    if not Supervisor.objects.filter(election=election, user=request.user).exists():
        data = {'election':      False,
                'error': _("You are not allowed to be here")
                }
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'election':      False,
                'error': _("The election has already begun")
                }
        return JsonResponse(data)

    grade = Grade.objects.create(name=name, code=code, election=election)

    data = {
        'success': True,
        'id_grade': grade.pk
    }

    return JsonResponse(data)


@login_required
def delete_grade(request, grade_id):
    """
    Ajax request to create a grade
    #TODO merge this function with class GradeDelete
    """

    try:
        grade = Grade.objects.get(pk=grade_id)
        election = grade.election
        supervisor = Supervisor.objects.get(election=election, user=request.user)
    except Election.DoesNotExist:
        data = {'error': _("The election does not exist")}
        return JsonResponse(data)
    except Grade.DoesNotExist:
        data = {'error': _("The grade does not exist")}
        return JsonResponse(data)
    except Supervisor.DoesNotExist:
        data = {'error': _("You are not allowed to be here")}
        return JsonResponse(data)

    if election.state != Election.DRAFT:
        data = {'error': _("The election has already begun")}
        return JsonResponse(data)

    grade.delete()
    data = {'success': True}

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
        election = self.object.election
        supervisor = Supervisor.objects.filter(election=election, user=self.request.user)
        return supervisor.exists()
