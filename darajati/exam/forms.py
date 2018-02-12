from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import Exam, Room


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        exclude = ['updated_on']


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        exclude = ['updated_on']
