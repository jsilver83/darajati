from django import forms
from .models import Attendance
from django.utils.translation import ugettext_lazy as _


class Attendance1Form(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendanceForm(forms.ModelForm):
    """
    Behavior: 
    - getting the tow fields from the model Attendance then add one more field to them
    by calling the super class in the initial state and adding the field 'student_name' as disabled inputText field
    
    - convert the enrollment field to a HiddenInput
    
    - add classes for css and re-order the list 
    """
    ORDER = ('student_name', 'status')

    def __init__(self, *args, **kwargs):
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.fields['student_name'] = forms.CharField(
            widget=forms.TextInput(attrs={'disabled': 'disabled', 'class': 'form-control'}), required=False)
        self.fields['id'] = forms.IntegerField(widget=forms.HiddenInput())
        self.fields['period'] = forms.CharField(
            widget=forms.TextInput(attrs={'disabled': 'disabled', 'class': 'form-control'}), required=False)
        self.order_fields(self.ORDER)

    class Meta:
        model = Attendance
        fields = ['enrollment', 'status', 'attendance_instance']
        labels = {
            'student_name': _('Student Name:')
        }
        widgets = {
            'enrollment': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'attendance_instance': forms.HiddenInput(),
        }

    def save(self, commit=True):
        self.instance.id = self.cleaned_data['id']
        self.instance.status = self.cleaned_data['status']
        if self.cleaned_data['status'] == 'pre':
            print("ignore")
        else:
            super(AttendanceForm, self).save()
