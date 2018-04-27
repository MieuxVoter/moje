from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.urls import reverse_lazy

from vote.models import *
from accounts.forms import *



class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'accounts/signup.html'



@login_required
def redirect_login(request):
    """
    This view is called when the user has just been logged in.
    We redirect the user according to her/his voter/supervisor profile
    """

    # look for a voter or supervisor profile
    voter = Voter.objects.get_or_create(user=request.user)[0]
    supervisors = Supervisor.objects.filter(user=request.user)
    if voter.election:
        return redirect('/vote/%d/'.format(voter.election.pk))
    elif supervisors.exists():
        return redirect('/election/dashboard/')
    else:
        return redirect('/voter/%d'.format(voter.pk))


@login_required
def user_detail(request, pk):
    user = User.objects.get(pk=pk)
    voter =  Voter.objects.filter(user=user)
    return render(request, 'accounts/voter_detail.html', {"voter":voter})

    
@login_required
def set_voter(request):
    """
    View for updating voter profile (referred as user profile)
    """
    form = UserForm(request.POST or None)

    #TODO
