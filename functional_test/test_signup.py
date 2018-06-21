import os
import poplib
import re
import time

from django.core import mail
from django.urls.base import reverse_lazy

from selenium.webdriver.common.keys import Keys

from .base import FunctionalTest


SUBJECT = 'Your login link for Superlists'


class LoginTest(FunctionalTest):


    def test_can_create_an_account(self):

        # Edith goes on the website
        self.browser.get(self.live_server_url)

        # She notices a "Sign up" button and clicks on it
        signup_btn = self.wait_for(self.browser.find_element_by_id, 'signup')
        signup_btn.click()

        # She creates an account
        inputbox = self.browser.find_element_by_id('id_username')
        self.wait_for(inputbox.send_keys, 'test_username')
        inputbox = self.browser.find_element_by_id('id_password1')
        self.wait_for(inputbox.send_keys, 'test_password')
        inputbox = self.browser.find_element_by_id('id_password2')
        self.wait_for(inputbox.send_keys, 'test_password')
        inputbox.send_keys(Keys.ENTER)
        signup_btn = self.wait_for(self.browser.find_element_by_id, 'signup')
        signup_btn.click()

        # She is on the dashboard now and she can start a new election
        create_btn = self.wait_for(self.browser.find_element_by_id, 'create_election')
        create_btn.click()

        # Now she logs out
        logout = str(reverse_lazy('logout'))
        self.browser.get(self.live_server_url + logout)
