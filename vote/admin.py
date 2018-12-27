from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.conf import settings

# Register your models here.
admin.site.register(User, UserAdmin)

if getattr(settings, "DEBUG", None):
    admin.site.register(Organisation)
    admin.site.register(Election)
    admin.site.register(Supervisor)
    admin.site.register(Voter)
    admin.site.register(Candidate)
    admin.site.register(Grade)
    admin.site.register(Rating)
    admin.site.register(GradeResult)
