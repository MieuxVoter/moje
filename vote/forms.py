from django import forms
from .models import Candidate, Grade
from django.forms.widgets import RadioSelect

def get_grades():
    ret = []
    for g in Grade.objects.all():
        ret.append( (g.id, "") )
    return ret

def form_grades(form):
    """ Returns the dictionary of candidates and grades given in the form """

    ret = {}

    # list all Candidates
    # FIXME list only in current election
    for c in Candidate.objects.all():
        g_id = int(form.cleaned_data['c.' + str(c.id)])
        try:
            grade = Grade.objects.get(pk=g_id)
        except Grade.DoesNotExist:
            return {}
        ret[c] = grade

    return ret

class VoteForm(forms.Form):

    def __init__(self, *args, **kwargs):

        super(VoteForm, self).__init__(*args, **kwargs)
        grades = get_grades()
        attrs     = {'template_name': 'vote/radio.html'}

        for c in Candidate.objects.all():
            name = c.user.first_name + " " + c.user.last_name
            form = forms.ChoiceField(label=name,
                                    choices=grades,
                                    widget=RadioSelect(attrs=attrs))
            self.fields["c." + str(c.id)] = form
