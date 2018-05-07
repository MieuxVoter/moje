from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from sesame import utils

from vote.models import *
from election.forms import *
from jmapp.settings import DEFAULT_FROM_EMAIL, PORT, DOMAIN



def find_election(election_id, check_user=None):
    """
    find election given its id or create a new one
    """

    election = get_object_or_404(Election, pk=election_id)

    if check_user and not Supervisor.objects.filter(election=election, user= check_user).exists():
        raise PermissionDenied("Vous ne gérez pas ce vote.")

    return election


def send_invite(voter):
    """
    Send a mail to the voter for an election
    """

    email = voter.user.email
    login_token = utils.get_parameters(voter.user)
    login_link = "http://{}:{:d}/vote/{}/?url_auth_token={}".format(
                            DOMAIN,
                            PORT,
                            voter.election.pk,
                            login_token['url_auth_token']
                          )
    name = voter.user.first_name.title() + " " + voter.user.last_name.title()
    html_message = """
    <p>Hello {},</p>
    <p>Vous avez été invité(e) à participer <a href="{}">au vote {}</a>. </p>
    <p>Si le lien ne fonctionne pas, vous pouvez copier-coller le lien suivant :</p>
    <p><a href="{}">{}</a></p>
    <p>Merci,</p>
    <p>Mieux Voter</p>
    """.format(name, login_link, voter.election.name, login_link, login_link)


    send_mail(
        'Mieux Voter',
        html_message,
        DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
        html_message = html_message
    )
