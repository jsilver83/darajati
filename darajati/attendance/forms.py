from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import Attendance


class PlainTextWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        if value is not None:
            field = "<input type='hidden' name='%s' value='%s' readonly> <span>%s</span>"\
                    %(name, mark_safe(value), mark_safe(value))
        else:
            field = "<input type='hidden' name='%s' value='' readonly> <span>-</span>" % (name)
        return field
        # return mark_safe(value) if value is not None else '-'


class AttendanceForm(forms.ModelForm):
    """
    Behavior:
    - getting the tow fields from the model Attendance then add one more field to them
    by calling the super class in the initial state and adding the field 'student_name' as disabled inputText field

    - convert the enrollment field to a HiddenInput

    - add classes for css and re-order the list
    """
    enrollment_id = forms.CharField(
        widget=PlainTextWidget)
    student_name = forms.CharField(
        widget=PlainTextWidget)
    student_university_id = forms.CharField(
        widget=PlainTextWidget)
    id = forms.IntegerField(widget=forms.HiddenInput())
    period = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'True', 'class': 'form-control'}), required=False)
    index = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    updated_by = forms.CharField(
        widget=PlainTextWidget, required=False)
    updated_on = forms.DateTimeField(widget=PlainTextWidget, required=False)

    ORDER = ('student_name', 'status')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.section = kwargs.pop('section')
        self.permissions = self.request.user.get_all_permissions()
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.order_fields(self.ORDER)
        if self.initial['status'] == Attendance.Types.EXCUSED \
                and 'attendance.can_give_excused_status' not in self.permissions:
            self.fields['status'].disabled = True

        if self.initial['updated_on'] and not self.section.course_offering.allow_change:
            self.fields['status'].disabled = True

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

    def clean_status(self):
        if 'attendance.can_give_excused_status' not in self.permissions \
                and self.cleaned_data.get('status') == Attendance.Types.EXCUSED\
                and 'status' in self.changed_data:
            self.add_error('status', _("You don't have permission to make this change"))
        return self.cleaned_data.get('status')
