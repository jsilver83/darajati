from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from enrollment.models import Instructor
from .models import Attendance, Excuse


class AttendanceForm(forms.ModelForm):

    ORDER = ('student_name', 'status')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        self.section = kwargs.pop('section')
        self.permissions = self.request.user.get_all_permissions()
        super(AttendanceForm, self).__init__(*args, **kwargs)
        self.order_fields(self.ORDER)

        self.fields['updated_by'].required = False

        # this condition is important to initialize this modelform with an instance. if a form has self.instance,
        # it will not create an object but rather update the object (i.e. the instance)
        if self.initial.get('id'):
            self.instance = get_object_or_404(Attendance, pk=self.initial.get('id'))

            # This readonly attribute added here is just a visual feedback. The actual prevention to change
            # the status (in such cases) is in the status_clean function below
            if (self.initial['status'] == Attendance.Types.EXCUSED and 'attendance.can_give_excused_status' not in self.permissions) \
                    or (self.initial['id'] and not self.section.course_offering.allow_change):
                self.fields['status'].widget.attrs.update({'readonly': 'readonly', 'class': 'form-control disabled'})

    class Meta:
        model = Attendance
        fields = '__all__'
        widgets = {
            'enrollment': forms.HiddenInput(),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'attendance_instance': forms.HiddenInput(),
        }

    def save(self, commit=True):
        if 'status' in self.changed_data:
            self.instance.updated_by = self.request.user
            return super(AttendanceForm, self).save(commit=commit)

    def clean_status(self):
        if 'status' in self.changed_data:
            if self.instance.status == Attendance.Types.EXCUSED:

                self.add_error('status', _("You can NOT change an excused status to something else."))
                return self.instance.status

            if self.instance.pk and not self.section.course_offering.allow_change \
                    and Instructor.is_active_coordinator(self.request.user.instructor):
                self.add_error('status', _("You can NOT change this status because it is un-changeable except by the "
                                           "coordinator."))
                return self.instance.status

            if 'attendance.can_give_excused_status' not in self.permissions \
                    and self.cleaned_data.get('status') == Attendance.Types.EXCUSED:
                self.add_error('status', _("You don't have permission to make this change"))
                return self.instance.status

        return self.cleaned_data.get('status')


class ExcuseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ExcuseForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            if field not in ['start_date', 'end_date', 'attachments']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Excuse
        fields = ['start_date', 'end_date', 'university_id', 'excuse_type', 'includes_exams', 'attachments',
                  'description']
        exclude = ['created_by', 'created_on', ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'datetimepicker3 form-control'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'datetimepicker3 form-control'}),
            'description': forms.Textarea,
            'includes_exams': forms.NullBooleanSelect,
        }

    def clean(self):
        cleaned_data = super(ExcuseForm, self).clean()
        absences_or_lates = Excuse.get_attendances(cleaned_data.get('university_id'),
                                                   cleaned_data.get('start_date'),
                                                   cleaned_data.get('end_date'),
                                                   [Attendance.Types.LATE, Attendance.Types.ABSENT])

        if not absences_or_lates:
            raise ValidationError(_('This student does NOT have any absence(s) or late(s) in the specified dates'))
        return cleaned_data
