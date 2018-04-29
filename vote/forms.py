from django import forms
from .models import Candidate, Grade, Election
from django.forms.widgets import RadioSelect
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField




def get_grades(election):
    ret = []
    for g in Grade.objects.filter(election=election):
        ret.append( (g.id, g.name) )
    return ret

def form_grades(form, election):
    """ Returns the dictionary of candidates and grades given in the form """

    ret = {}

    # list all Candidates
    candidates = Candidate.objects.filter(election=election)
    for c in candidates:
        g_id = int(form.cleaned_data['c.' + str(c.id)])
        try:
            grade = Grade.objects.get(pk=g_id)
        except Grade.DoesNotExist:
            return {}
        ret[c] = grade

    return ret


class VoteForm(forms.Form):
    """
    Create a form with majority judgment grades

    .note: should it use instead a meta form?

    """

    def __init__(self, *args, **kwargs):
        self.election = kwargs.pop('election')

        super(VoteForm, self).__init__(*args, **kwargs)

        grades    = get_grades(self.election)
        candidates = Candidate.objects.filter(election=self.election)

        for c in candidates:
            name = c.user.first_name + " " + c.user.last_name
            form = forms.ChoiceField(label=name,
                                    choices=grades,
                                    widget=RadioSelect())
            self.fields["c." + str(c.id)] = form
