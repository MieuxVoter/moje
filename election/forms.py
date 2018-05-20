from django import forms
from django.forms.widgets import RadioSelect
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from vote.models import *


class FutureDateField(forms.DateField):
    """ Validator for only date in the future """

    def validate(self, value):
        super().validate(value)
        if value < timezone.now().date():
            raise ValidationError(_("The date is not in the future"))


class GeneralStepForm(forms.Form):
    def __init__(self,*args,**kwargs):
        self.disabled = kwargs.pop('disabled') if 'disabled' in kwargs else False
        super(GeneralStepForm,self).__init__(*args,**kwargs)
        self.fields['name'].disabled = self.disabled
        self.fields['note'].disabled = self.disabled

    name    = forms.CharField(
                    label=_("Election name"),
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

    note = forms.CharField(label=_("Question"),
                        widget=forms.Textarea(attrs={'class': "form-control"}))




class ConfigStepForm(forms.Form):

    voting_system    = forms.CharField(
                    label=_("Voting system"),
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                            )


class ConfirmStepForm(forms.Form):
    pass


class CreateCandidateForm(forms.Form):
    first_name    = forms.CharField(label=_("First name"),
                                    max_length=200,
                                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':_("First name")})
                                    )

    last_name    = forms.CharField(
                    label=_("Name"),
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':_("Name")})
                            )

    program    = forms.CharField(
                    label=_("Information"),
                    max_length=200,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder':_("Information")})
                            )



class VotersListStepForm(forms.Form):
    def __init__(self,*args,**kwargs):
        super(VotersListStepForm,self).__init__(*args,**kwargs)

    list = forms.CharField(
                    label=_("Voters list"),
                    widget=forms.Textarea(attrs={'class': 'form-control'}))
