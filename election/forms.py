from django import forms
from django.forms.widgets import RadioSelect
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField
from django.core.exceptions import ValidationError

from datetime import datetime

from vote.models import *


class FutureDateField(forms.DateField):
    """ Validator for only date in the future """

    def validate(self, value):
        super().validate(value)
        if value < datetime.now().date():
            raise ValidationError("La date n'est pas postérieure à aujourd'hui.")


class GeneralStepForm(forms.Form):

    name    = forms.CharField(
                    label="Nom de l'élection",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )
    start   = FutureDateField(
                    label="Date de début",
                    widget=forms.DateInput(attrs={'class': "form-control"}),
                    input_formats=['%d/%m/%Y'],
                    localize=True
                                )
    end     = FutureDateField(
                    label="Date de fin",
                    widget=forms.DateInput(attrs={'class': "form-control"}),
                    input_formats=['%d/%m/%Y'],
                    localize=True
                                )

    # state   = forms.ChoiceField(
    #                     label="État de l'élection",
    #                     choices=Election.STATE_ELECTION,
    #                     widget=forms.RadioSelect()
    #                 )
    note    = forms.CharField(
                    label="Ajouter une note",
                    widget=forms.Textarea(attrs={'class': "form-control"})
                            )




class ConfigStepForm(forms.Form):

    voting_system    = forms.CharField(
                    label="Système de vote",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )


class CreateCandidateForm(forms.Form):
    name    = forms.CharField(
                    label="Nom",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )

    program    = forms.CharField(
                    label="Programme",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )
