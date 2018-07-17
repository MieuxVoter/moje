import os
import re
import time

from django.test import TestCase
from django.conf import settings
from django.core import mail
from django.core.exceptions import FieldError
from django.urls.base import reverse_lazy
from django.test.client import Client
from django.contrib import auth

from selenium.webdriver.common.keys import Keys

from utils.test import FunctionalTest
from vote.models import User, Election, Candidate, Voter, Supervisor
from election import views



class ElectionCreationTest(FunctionalTest):

    def test_a_basic_election(self):

        # Edith goes on the website and is automatically connected
        self.auto_login()
        self.browser.get(self.live_server_url)

        # She notices a "Create an election" button and clicks on it
        create_btn = self.wait_for(self.browser.find_element_by_id, 'create_election')
        create_btn.click()

        # She adds general settings
        inputbox = self.browser.find_element_by_id('id_name')
        self.wait_for(inputbox.send_keys, 'Test election')
        inputbox = self.browser.find_element_by_id('id_note')
        self.wait_for(inputbox.send_keys, 'To be or not to be?')
        btn = self.wait_for(self.browser.find_element_by_id, 'submit')
        btn.click()

        # She adds some candidates
        for i in range(5):
            inputbox = self.browser.find_element_by_id('id_label')
            self.wait_for(inputbox.send_keys, 'Fakecandidate')
            inputbox = self.browser.find_element_by_id('id_description')
            self.wait_for(inputbox.send_keys, 'Fake program')
            btn = self.wait_for(self.browser.find_element_by_id, 'form-btn')
            btn.click()
            inputvalue = inputbox.get_attribute('value')
            self.assertEqual(inputvalue, "")
            text = self.wait_for(self.browser.find_elements_by_xpath, "//*[contains(text(), 'Number"+str(i)+"')]")

        # She adds some voters
        self.browser.find_element_by_id('go_voters').click()

        for i in range(5):
            inputbox = self.browser.find_element_by_id('first_name')
            self.wait_for(inputbox.send_keys, 'Fakevoter')
            inputbox = self.browser.find_element_by_id('last_name')
            self.wait_for(inputbox.send_keys, 'Number' + str(i))
            inputbox = self.browser.find_element_by_id('email')
            self.wait_for(inputbox.send_keys, 'fake' + str(i) + '@example.com')
            self.browser.find_element_by_id('form-btn').click()
            text = self.wait_for(self.browser.find_elements_by_xpath, "//*[contains(text(), 'fake " + str(i) + "@example.com')]")

        # She adds also voters from a list
        self.browser.find_element_by_id('go_list').click()
        inputbox = self.browser.find_element_by_id('id_list')
        for i in range(5, 10):
            voter = 'Number%d, Fakevoter, fake%d@example.com\n' % (i,i)
            self.wait_for(inputbox.send_keys, voter)
        self.browser.find_element_by_id('form-btn').click()

        # Finally she starts the election
        start = self.wait_for(self.browser.find_element_by_id, 'go_start')
        start.click()


class ElectionDeleteTest(TestCase):

    def setUp(self):
        # create the client
        self.client = Client()
        self.user = User.objects.create_user("fred", "fred@test.fr", "secret")
        self.client.login(username="fred", password="secret")
        self.assertEqual(self.user, auth.get_user(self.client))

        # create the election with its candidates and voters
        self.election = Election.objects.create(name="lion", note="roar")
        self.supervisor = Supervisor.objects.create(election=self.election,
                                                    user=self.user)
        self.users = []
        self.candidates = []
        self.voters = []

        for i in range(5):
            u = User.objects.create(username="test {:d}".format(i))
            self.users.append(u)
            c = Candidate.objects.create(election=self.election)
            self.candidates.append(c)
            v = Voter.objects.create(election=self.election, user=u)
            self.voters.append(v)


    def test_delete_election(self):
        """When an election is deleted, its users (only if they don't have elections anymore) and its candidates are also deleted"""

        e_pk = self.election.pk
        c_pks = [candidate.pk for candidate in self.candidates]
        v_pks = [voter.pk for voter in self.voters]
        u_pks = [user.pk for user in self.users]


        response = self.client.post('/election/manage/delete_election/%d/'%e_pk,
                                    {'pk': e_pk})

        try:
            Election.objects.get(pk=e_pk)
            raise FieldError("The election was not deleted")
        except Election.DoesNotExist:
            pass

        for pk in c_pks:
            try:
                Candidate.objects.get(pk=pk)
                raise FieldError("The candidate was not deleted")
            except Candidate.DoesNotExist:
                pass

        for pk in u_pks:
            try:
                User.objects.get(pk=pk)
                raise FieldError("The user was not deleted")
            except User.DoesNotExist:
                pass

        for pk in v_pks:
            try:
                Voter.objects.get(pk=pk)
                raise FieldError("The voter was not deleted")
            except Voter.DoesNotExist:
                pass
