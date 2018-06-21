from django.test import TestCase

# Create your tests here.
import os
import poplib
import re
import time

from django.core import mail
from django.urls.base import reverse_lazy

from selenium.webdriver.common.keys import Keys

from functional_test.base import FunctionalTest


SUBJECT = 'Your login link for Superlists'


class ElectionCreationTest(FunctionalTest):


    def test_can_create_an_account(self):

        # Edith goes on the website and is automatically connected
        self.client.login(username="edith", password='password1')
        cookie = self.client.cookies['sessionid']
        self.browser.get(self.live_server_url)  #selenium will set cookie domain based on current page domain
        self.browser.add_cookie({'name': 'sessionid', 'value': cookie.value, 'secure': False, 'path': '/'})
        self.browser.refresh() #need to update page for logged in user
        self.browser.get(self.live_server_url)
