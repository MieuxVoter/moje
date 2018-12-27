from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _



class Organisation(models.Model):
    name        = models.CharField(max_length=200, blank=True)
    site        = models.URLField(max_length=200, blank=True)


class User(AbstractUser):
    picture = models.FilePathField(path="/static/dashboard/img/user/", default='blank.png')
    bio = models.TextField(max_length=500, blank=True)
    street = models.TextField(max_length=200, blank=True)
    city = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=30, blank=True)
    postcode = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    email = models.EmailField(_('email address'), blank=True, null=True, unique=True)
    password_token = models.CharField(max_length=100, blank=True)
    password_token_validity = models.DateTimeField(null=True, blank=True)

    def clean(self):
        """
        Clean up blank fields to null
        """
        if self.email == "":
            self.email = None



class Election(models.Model):
    """
    Manage an Election
    """

    START = 'ST'
    DRAFT = 'DR'
    OVER  = 'OV'
    STATE_ELECTION = (
        (START, 'En cours'),
        (DRAFT, 'Brouillon'),
        (OVER,  'Terminée')
    )

    name        = models.CharField(max_length=200, default="")
    note        = models.TextField(default="")
    picture     = models.FilePathField(path="/static/dashboard/img/election/", default='blank.png')
    start       = models.DateField(null=True, blank=True)
    end         = models.DateField(null=True, blank=True)
    state       = models.CharField(
                            max_length=2,
                            choices=STATE_ELECTION,
                            default=DRAFT,
                        )
    belenios_uuid = models.CharField(null=False, max_length=50)
    is_anonymous = models.BooleanField(null=False)


class Supervisor(models.Model):
    """
    A supervisor is an extended user. A supervisor is in charge of one or several elections.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE, default=None, null=True)


class Voter(models.Model):
    """
    A voter is an extended user
    """
    user        = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True)
    election    = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    ballot      = models.CharField(null=True, max_length=200)

    def __str__(self):
        return '{} {} {}'.format(self.user.first_name, self.user.last_name, self.user.email)



class Candidate(models.Model):
    """
    This model represents a candidate in the election.
    """
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    label = models.TextField(default="")
    description = models.TextField(default="")
    program = models.TextField(default="")


class Grade(models.Model):
    """
    A grade is a judgment
    """
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    name = models.CharField(max_length=200, default="")
    code = models.CharField(max_length=10, default="")


class GradeResult(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, default=None)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, default=None, null=True)
    result = models.FloatField(null=True, blank=True)

    def grade_str(self):
        return self.grade.name

    def candidate_str(self):
        return self.candidate.label


class Rating(models.Model):
    """
    Record a Grade given from a Voter to a Candidate
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, default=None)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, default=None)
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, default=None)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, default=None, null=True)
