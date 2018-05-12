from django import forms
from django.forms.widgets import RadioSelect
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField
from django.core.exceptions import ValidationError
from django.utils import timezone

from vote.models import *


class FutureDateField(forms.DateField):
    """ Validator for only date in the future """

    def validate(self, value):
        super().validate(value)
        if value < timezone.now().date():
            raise ValidationError("La date n'est pas postérieure à aujourd'hui.")


class GeneralStepForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.disabled = kwargs.pop('disabled') if 'disabled' in kwargs else False
        super(GeneralStepForm,self).__init__(*args,**kwargs)
        self.fields['name'].disabled = self.disabled
        self.fields['note'].disabled = self.disabled

    name    = forms.CharField(
                    label="Nom de l'élection",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'}))

    # start   = FutureDateField(
    #                 label="Date de début",
    #                 widget=forms.DateInput(attrs={'class': "form-control"}),
    #                 input_formats=['%d/%m/%Y'],
                        # disabled=self.disabled
    #                             )
    # end     = FutureDateField(
    #                 label="Date de fin",
    #                 widget=forms.DateInput(attrs={'class': "form-control"}),
    #                 input_formats=['%d/%m/%Y'],
    # disabled=self.disabled
    #                             )

    note = forms.CharField(label="Question",
                        widget=forms.Textarea(attrs={'class': "form-control"}))




class ConfigStepForm(forms.Form):

    voting_system    = forms.CharField(
                    label="Système de vote",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )


class ConfirmStepForm(forms.Form):
    pass


class CreateCandidateForm(forms.Form):
    first_name    = forms.CharField(label="Prénom",
                                    max_length=200,
                                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Prénom'})
                                    )

    last_name    = forms.CharField(
                    label="Nom",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Nom'})
                            )

    program    = forms.CharField(
                    label="Programme",
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Programme'})
                            )



class VotersListStepForm(forms.Form):
    def __init__(self,*args,**kwargs):
        super(VotersListStepForm,self).__init__(*args,**kwargs)

    list = forms.CharField(
                    label="Liste des électeurs",
                    widget=forms.Textarea(attrs={'class': 'form-control'}))
