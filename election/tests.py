import os
import re
import time

from django.test import TestCase
from django.conf import settings
from django.core import mail
from django.urls.base import reverse_lazy

from selenium.webdriver.common.keys import Keys

from utils.test import FunctionalTest


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
            inputbox = self.browser.find_element_by_id('id_first_name')
            self.wait_for(inputbox.send_keys, 'Fakecandidate')
            inputbox = self.browser.find_element_by_id('id_last_name')
            self.wait_for(inputbox.send_keys, 'Number' + str(i))
            inputbox = self.browser.find_element_by_id('id_program')
            self.wait_for(inputbox.send_keys, 'Fake program')
            btn = self.wait_for(self.browser.find_element_by_id, 'form-btn')
            btn.click()
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
