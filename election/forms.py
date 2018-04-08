from django import forms
from vote.models import *
from django.forms.widgets import RadioSelect
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField









class GeneralStepForm(forms.Form):

    name    = forms.CharField(
                    label="Nom de l'élection",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )
    start   = forms.DateTimeField(
                    label="Date de début",
                    widget=forms.DateInput(attrs={'class': "form-control"})
                                )
    end     = forms.DateTimeField(
                    label="Date de fin",
                    widget=forms.DateInput(attrs={'class': "form-control"})
                                )

    # state   = forms.ChoiceField(
    #                     label="État de l'élection",
    #                     choices=Election.STATE_ELECTION,
    #                     widget=forms.RadioSelect()
    #                 )
    # note    = forms.CharField(
    #                 label="Ajouter une note",
    #                 widget=forms.Textarea(attrs={'class': "form-control"})
    #                         )




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
