from django import forms
from .models import Attendance
from django.utils.translation import ugettext_lazy as _


class AttendanceForm(forms.ModelForm):
    """
    Behavior: 
    - getting the tow fields from the model Attendance then add one more field to them
    by calling the super class in the initial state and adding the field 'enrollment_id' as a hidden field
    
    - convert the enrollment field to a textInput then make it disable from change
    """
    def __init__(self, *args, **kwargs):
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.fields['enrollment_id'] = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Attendance
        fields = ['enrollment', 'status']
        labels = {
            'enrollment': _('Student Name:')
        }
        widgets = {
            'enrollment': forms.TextInput(attrs={'disabled': 'disabled'}),
        }
