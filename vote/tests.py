import os
import re
import time

from django.test import TestCase
from django.conf import settings
from django.urls.base import reverse_lazy
from django.test.client import Client
from django.contrib import auth
from django.test.utils import override_settings


from utils.test import FunctionalTest
from vote.models import User, Election, Candidate, Voter, Grade
from election import views
from sesame import utils


@override_settings(DEBUG=True)
class VotingTest(FunctionalTest):


    def test_a_vote(self):
        # creating a fake election
        election = Election.objects.create(name="lion", state=Election.START)
        [Candidate.objects.create(
                            label="Opt %d"%i,
                            election=election)  for i in range(5)]
        user = User.objects.create_user("Fred", "fred@polo.fr", "secret")
        Voter.objects.create(user=user, election=election)
        Grade.objects.create(name="Excellent", election=election, code="ex")
        Grade.objects.create(name="Very good", election=election, code="tb")
        Grade.objects.create(name="Good", election=election, code="b")
        Grade.objects.create(name="Fair", election=election, code="p")
        Grade.objects.create(name="Poor", election=election, code="ins")
        Grade.objects.create(name="To Reject", election=election, code="rej")


        # Fred clicks on the link on his mail invitation.
        login_token = utils.get_parameters(user)['url_auth_token']
        login_link = "/vote/{}/?url_auth_token={}".format(election.pk,
                                                          login_token)

        self.browser.get(self.live_server_url + login_link)

        # Fred always chooses excellent
        # time.sleep(60)
        for i in range(5):
            radio = self.wait_for(self.browser.find_element_by_id, 'id_c.{:d}_0'.format(i+1))
            self.browser.execute_script("arguments[0].click();", radio)

        # Fred validates his votes and is redirected
        self.browser.find_element_by_id("cast").click()
        url = self.live_server_url + "/vote/{:d}/success/".format(election.pk)
        self.wait_for(self.assertEqual, url, self.browser.current_url)

        # Fred tries to access to the result, but the vote is still opened
        self.wait_for(self.browser.find_element_by_id, "go_results").click()
        self.wait_for(self.browser.find_element_by_class_name, "error")

        # Someone closes the vote in the meantime, so Fred can access to the results
        election.state = Election.OVER
        election.save()
        self.wait_for(self.browser.find_element_by_id, "go_results").click()
        self.wait_for(self.browser.find_element_by_class_name, "results")
