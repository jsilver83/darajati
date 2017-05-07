from django import forms
from .models import Attendance
from django.utils.translation import ugettext_lazy as _


class AttendanceForm(forms.ModelForm):
    """
    Behavior: 
    - getting the tow fields from the model Attendance then add one more field to them
    by calling the super class in the initial state and adding the field 'student_name' as disabled inputText field
    
    - convert the enrollment field to a HiddenInput
    
    - add classes for css and re-order the list 
    """
    student_name = forms.CharField(
        widget=forms.TextInput(attrs={'disabled': 'disabled', 'class': 'form-control'}), required=False)
    student_university_id = forms.CharField(
        widget=forms.TextInput(attrs={'disabled': 'disabled', 'class': 'form-control'}), required=False)
    id = forms.IntegerField(widget=forms.HiddenInput())
    period = forms.CharField(
        widget=forms.TextInput(attrs={'disabled': 'disabled', 'class': 'form-control'}), required=False)
    index = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    updated_by = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'disabled': 'disabled'}), required=False)
    updated_on = forms.DateTimeField(widget=forms.DateTimeInput(
        attrs={'disabled': 'disabled'}), required=False)

    ORDER = ('student_name', 'status')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.permissions = self.request.user.get_all_permissions()
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.order_fields(self.ORDER)
        if self.initial['status'] == Attendance.Types.EXCUSED:
            self.fields['status'].widget.attrs['readonly'] = True

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
        if self.cleaned_data['id']:
            self.instance.id = self.cleaned_data['id']

        if 'status' in self.changed_data:
            self.instance.updated_by = self.user
            return super(AttendanceForm, self).save()
