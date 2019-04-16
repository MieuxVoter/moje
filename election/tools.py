from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.utils.text import format_lazy
from sesame import utils

from vote.models import *
from election.forms import *
from moje.settings import DEFAULT_FROM_EMAIL, PORT, DOMAIN



def find_election(election_id, check_user=None):
    """
    find election given its id or create a new one
    """

    election = get_object_or_404(Election, pk=election_id)

    if check_user and not Supervisor.objects.filter(election=election, user= check_user).exists():
        raise PermissionDenied(_("You are not a supervisor of this election"))

    return election


def send_invite(voter):
    """
    Send a mail to the voter for an election
    """

    email = voter.user.email
    login_token = utils.get_parameters(voter.user)

    if PORT != 80:
        login_link = "http://{}:{:d}/vote/{}/?url_auth_token={}".format(
                            DOMAIN,
                            PORT,
                            voter.election.pk,
                            login_token['url_auth_token']
                          )
    else:
        login_link = "http://{}/vote/{}/?url_auth_token={}".format(
                            DOMAIN,
                            voter.election.pk,
                            login_token['url_auth_token']
                          )

    name = voter.user.first_name.title() + " " + voter.user.last_name.title()
    html_message = format_lazy("""
    <p>Dear {name},</p>
    <p>You have been invited to participate to <a href="{login_link}"> {election_name}</a>. </p>
    <p>If this link does not work, you can copy/paste the following link:</p>
    <p><a href="{login_link}">{login_link}</a></p>
    <p>Thanks,</p>
    <p>Mieux Voter</p>
    """, name=name, login_link=login_link, election_name=voter.election.name)


    send_mail(
        _('Invite to vote at ') + voter.election.name,
        html_message,
        DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
        html_message=html_message
    )
