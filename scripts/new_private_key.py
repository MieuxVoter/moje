#!/usr/bin/env python

# Code snippet from https://stackoverflow.com/a/16630719/4986615

from django.utils.crypto import get_random_string

chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
print(get_random_string(50, chars))
