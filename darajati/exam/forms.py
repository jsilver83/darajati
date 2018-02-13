from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import Exam, Room, Examiner


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        exclude = ['updated_on']


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        exclude = ['updated_on']


class ExaminerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.exams = self.request = kwargs.pop('exams_list', None)
        super(ExaminerForm, self).__init__(*args, **kwargs)
        self.fields['exam'] = forms.ChoiceField(
            required=True,
            choices=(('', '---------'),) + tuple(self.exams),
            widget=forms.Select(
                attrs={'class': 'thm-field'}
            )
        )

    class Meta:
        model = Examiner
        exclude = ['updated_on', 'updated_by']
        widgets = {
            'instructor': forms.Select(attrs={'class': 'thm-field'}),
            'generosity_factor': forms.NumberInput(attrs={'class': 'thm-field'}),
            'order': forms.NumberInput(attrs={'class': 'thm-field'}),
        }

    def clean_exam(self):
        exam = self.cleaned_data['exam']
        self.cleaned_data['exam'] = Exam.objects.get(id=exam)
        return self.cleaned_data['exam']
