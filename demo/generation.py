# -*- coding: utf-8 -*-
# Written by null-none https://github.com/null-none/random-user-generation

from urllib.request import urlopen
import json

URL = 'https://randomuser.me/api/'


class RandomUserGeneration(object):
    data = {}

    def __init__(self):
        self.data = json.loads(urlopen(URL).read())

    def get_location(self):
        return self.data['results'][0]['location']['street']

    def get_city(self):
        return self.data['results'][0]['location']['city']

    def get_state(self):
        return self.data['results'][0]['location']['state']

    def get_first_name(self):
        return self.data['results'][0]['name']['first']

    def get_last_name(self):
        return self.data['results'][0]['name']['last']

    def get_postcode(self):
        return self.data['results'][0]['location']['postcode']

    def get_phone(self):
        return self.data['results'][0]['phone']

    def get_mail(self):
        return self.data['results'][0]['email']

    def get_username(self):
        return self.data['results'][0]['login']['username']

    def get_gender(self):
        return self.data['results'][0]['gender']

    def get_picture(self):
        return self.data['results'][0]['picture']['large']
