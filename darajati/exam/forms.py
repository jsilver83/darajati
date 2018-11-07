from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet

from grade.models import GradeFragment
from .utils import ordinal, get_allowed_markers_for_a_fragment
from .models import *
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        exclude = ['updated_on']


class ExamSettingsForm(forms.ModelForm):

    class Meta:
        model = GradeFragment
        fields = ['exam_date', 'allow_markers_from_other_courses', 'allow_markers_to_mark_own_students',
                  'markings_difference_tolerance', 'number_of_markers', 'default_tie_breaking_marker', ]

        widgets = {
            'exam_date': forms.DateTimeInput(attrs={'class': 'form-control datetimepicker3'}),
        }

    def __init__(self, *args, **kwargs):
        self.fragment = kwargs.pop('fragment')
        super(ExamSettingsForm, self).__init__(*args, **kwargs)

        self.fields['default_tie_breaking_marker'].queryset = get_allowed_markers_for_a_fragment(self.fragment, True)


class ExamShiftForm(forms.ModelForm):

    class Meta:
        model = ExamShift
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control datetimepicker3'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control datetimepicker3'}),
        }

    def __init__(self, *args, **kwargs):
        self.fragment = kwargs.pop('fragment')
        super(ExamShiftForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ExamShiftForm, self).clean()
        start_date = cleaned_data['start_date']
        end_date = cleaned_data['end_date']

        if start_date >= end_date:
            raise forms.ValidationError(_('Start Time should be less than End Time'))

        return cleaned_data

    def save(self, commit=True):
        saved = super(ExamShiftForm, self).save(commit=False)
        saved.fragment = self.fragment
        if commit:
            saved.save()
        return saved


class ExamShiftsFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(ExamShiftsFormSet, self).__init__(*args, **kwargs)


class ExamRoomForm(forms.ModelForm):

    class Meta:
        model = ExamRoom
        fields = ['exam_shift', 'room', 'capacity']

    def __init__(self, *args, **kwargs):
        self.fragment = kwargs.pop('fragment')
        super(ExamRoomForm, self).__init__(*args, **kwargs)
        self.fields['exam_shift'].queryset = ExamShift.objects.filter(fragment=self.fragment)
        self.fields['exam_shift'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        return '%s - %s' % (obj.start_date.astimezone().time(),
                            obj.end_date.astimezone().time())


class ExamRoomsFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(ExamRoomsFormSet, self).__init__(*args, **kwargs)


class MarkerForm(forms.ModelForm):

    class Meta:
        model = Marker
        fields = ['instructor', 'exam_room', 'order', 'generosity_factor', 'is_a_monitor']

    def __init__(self, *args, **kwargs):
        self.fragment = kwargs.pop('fragment')
        super(MarkerForm, self).__init__(*args, **kwargs)
        self.fields['exam_room'].queryset = ExamRoom.objects.filter(exam_shift__fragment=self.fragment)
        self.fields['generosity_factor'].widget.attrs.update({'style': 'width: 70px'})
        self.fields['generosity_factor'].widget.attrs.update({'step': '0.5'})
        self.fields['instructor'].widget.attrs.update({'style': 'width: 200px'})

        if self.fragment.allow_markers_from_other_courses:
            department = self.fragment.course_offering.course.department
            self.fields['instructor'].queryset = \
                Instructor.objects.filter(
                    assigned_periods__section__course_offering__course__department=department
                ).distinct()
        else:
            periods = ScheduledPeriod.objects.filter(section__course_offering=self.fragment.course_offering)
            self.fields['instructor'].queryset = Instructor.objects.filter(
                pk__in=periods.values('instructor_assigned').distinct()
            )


class MarkersFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(MarkersFormSet, self).__init__(*args, **kwargs)

    def clean(self):
        if any(self.errors):
            return

        markers = []
        monitors_shifts = []
        for form in self.forms:
            instructor = form.cleaned_data['instructor']
            exam_room = form.cleaned_data['exam_room']
            is_a_monitor = form.cleaned_data['is_a_monitor']
            marker = {'i': instructor, 'r': exam_room}

            if marker in markers:
                raise forms.ValidationError(
                    _('You can not assign marker (%s) multiple times to the same room.') % marker.get('i'))
            markers.append(marker)

            if is_a_monitor:
                monitor_shift = {'i': instructor, 's': exam_room.exam_shift.pk}
                if monitor_shift in monitors_shifts:
                    raise forms.ValidationError(
                        _('You can not assign monitor (%s) multiple times to the same shift.') % monitor_shift.get('i'))
                monitors_shifts.append(monitor_shift)


class StudentMarkForm(forms.ModelForm):
    is_present = forms.NullBooleanField(label=_('Is Present?'), widget=forms.CheckboxInput)

    class Meta:
        model = StudentMark
        fields = ['student_placement', 'marker', 'mark']
        widgets = {
            'student_placement': forms.HiddenInput,
            'marker': forms.HiddenInput
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(StudentMarkForm, self).__init__(*args, **kwargs)
        self.fields['mark'].required = False
        self.fields['mark'].widget.attrs.update({'style': 'width:75px', 'class': 'grade_quantity'})
        if self.instance.marker.is_a_monitor:
            self.initial['is_present'] = self.instance.student_placement.is_present
        else:
            del self.fields['is_present']

    def clean(self):
        cleaned_data = super(StudentMarkForm, self).clean()
        mark = cleaned_data['mark']

        if self.instance.marker.is_a_monitor:
            is_present = cleaned_data.get('is_present')
            if is_present and not mark:
                raise forms.ValidationError(_("This student is marked as present but you didn't give him a mark"))
            if not is_present and mark:
                raise forms.ValidationError(_("This student is marked as absent but you gave him a mark"))
        else:
            if self.instance.student_placement.is_present and not mark:
                raise forms.ValidationError(_("This student is marked as present but you didn't give him a mark"))

            if not self.instance.student_placement.is_present and mark:
                raise forms.ValidationError(_("This student is marked as absent but you gave him a mark"))

        return cleaned_data

    def save(self, commit=True):
        saved = super(StudentMarkForm, self).save(commit=False)
        saved.updated_by = self.user

        if commit:
            saved.save()

        if 'is_present' in self.changed_data:
            self.instance.student_placement.is_present = self.cleaned_data.get('is_present')
            self.instance.student_placement.save()

        return saved


class StudentMarkFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(StudentMarkFormSet, self).__init__(*args, **kwargs)
