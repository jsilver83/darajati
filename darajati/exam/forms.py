from django import forms
from django.utils.translation import ugettext_lazy as _

from grade.models import GradeFragment


class SubjectiveGradeFragmentForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.fragments = self.request = kwargs.pop('fragments', None)
        super(SubjectiveGradeFragmentForm, self).__init__(*args, **kwargs)
        self.fields['grade_fragment'] = forms.ChoiceField(
            label=_('Grade fragment'),
            required=True,
            choices=self.fragments,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        self.fields['number_of_rooms'] = forms.IntegerField(
            label=_('Number of rooms'),
            required=True,
            min_value=1,
            widget=forms.NumberInput(attrs={'class': 'form-control'})
        )

    # def __init__(self, *args, **kwargs):
    #     super(SubjectiveGradeFragmentForm, self).__init__()
    #     self.fields['']


class ExamsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ExamsForm, self).__init__(*args, **kwargs)
        self.fields['grade_fragment'] = forms.CharField(
            label=_('Grade fragment'),
            required=False,
            widget=forms.Select(attrs={'class': 'form-control'})
        )