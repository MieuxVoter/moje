from django.db import models
from django.contrib.auth.models import AbstractUser



class Election(models.Model):
    """
    Manage an Election
    """
    name        = models.CharField(max_length=200, default="")
    picture     = models.FilePathField(path="/static/dashboard/img/user/", default='blank.png')


class User(AbstractUser):
    pass


class Candidate(models.Model):
    """
    This model represents a candidate in the election.
    """
    election    = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    picture     = models.FilePathField(path="/static/dashboard/img/user/", default='blank.png')
    bio         = models.TextField(max_length=500, blank=True)
    street      = models.TextField(max_length=200, blank=True)
    city        = models.CharField(max_length=30, blank=True)
    state       = models.CharField(max_length=30, blank=True)
    postcode    = models.CharField(max_length=30, blank=True)
    birth_date  = models.DateField(null=True, blank=True)


class Voter(models.Model):
    """
    A voter is an extended user
    """
    user        = models.OneToOneField(User, on_delete=models.CASCADE)
    picture     = models.FilePathField(path="/static/dashboard/img/user/", default='blank.png')
    bio         = models.TextField(max_length=500, blank=True)
    street      = models.TextField(max_length=200, blank=True)
    city        = models.CharField(max_length=30, blank=True)
    state       = models.CharField(max_length=30, blank=True)
    postcode    = models.CharField(max_length=30, blank=True)
    birth_date  = models.DateField(null=True, blank=True)

class Grade(models.Model):
    """
    A grade is a judgment
    """
    election    = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    name        = models.CharField(max_length=200, default="")
    code        = models.CharField(max_length=10, default="")

class Rating(models.Model):
    """
    Record a Grade given from a Voter to a Candidate
    """
    candidate   = models.ForeignKey(Candidate, on_delete=models.CASCADE, default=None)
    voter       = models.ForeignKey(Voter, on_delete=models.CASCADE, default=None)
    grade       = models.ForeignKey(Grade, on_delete=models.CASCADE, default=None)
