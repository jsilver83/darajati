from decimal import Decimal

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet
from django.utils.translation import ugettext_lazy as _

from darajati.utils import decimal
from enrollment.utils import today
from .models import StudentGrade, GradeFragment


class GradesForm(forms.ModelForm):
    class Meta:
        model = StudentGrade
        fields = ['enrollment', 'grade_fragment', 'grade_quantity', 'remarks', ]
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'thm-field'}),
            'enrollment': forms.HiddenInput(),
            'grade_fragment': forms.HiddenInput(),
        }

    def __init__(self, user, is_change_allowed, *args, **kwargs):
        self.is_change_allowed = is_change_allowed
        self.user = user

        super(GradesForm, self).__init__(*args, **kwargs)

        if self.instance.grade_fragment.entry_in_percentages:
            self.fields['grade_percentage'] = forms.DecimalField(
                decimal_places=settings.MAX_DECIMAL_POINT,
                max_digits=settings.MAX_DIGITS,
                required=False,
                max_value=100, min_value=0,
                widget=forms.NumberInput(attrs={'class': 'thm-field grade_quantity'}))

            self.fields['grade_quantity'].required = False

            if self.instance.grade_quantity is not None:
                self.initial['grade_percentage'] = \
                    decimal(self.instance.grade_quantity * 100 / self.instance.grade_fragment.weight)

        elif not self.instance.grade_fragment.entry_in_percentages:
            max_value = self.instance.grade_fragment.weight

            self.fields['grade_quantity'] = forms.DecimalField(
                decimal_places=settings.MAX_DECIMAL_POINT,
                max_digits=settings.MAX_DIGITS,
                max_value=max_value, min_value=0,
                required=False,
                widget=forms.NumberInput(attrs={'class': 'thm-field grade_quantity'}))

        for field in self.fields:
            if field in ['grade_percentage', 'grade_quantity', 'remarks'] and not self.is_change_allowed:
                self.fields[field].widget.attrs.update({'readonly': 'True'})

    def clean(self):
        cleaned_data = super().clean()
        if ('grade_percentage' in self.changed_data or 'grade_quantity' in self.changed_data
                or 'remarks' in self.changed_data) and not self.is_change_allowed:
            raise forms.ValidationError(_('You are not allowed to tamper with the grades'))
        return cleaned_data

    def save(self, commit=True):
        self.instance.updated_by = self.user
        if self.instance.grade_fragment.entry_in_percentages and self.cleaned_data['grade_percentage'] is not None:
            self.instance.grade_quantity = (self.instance.grade_fragment.weight / 100) * self.cleaned_data[
                'grade_percentage']
        return super(GradesForm, self).save()


class BaseGradesFormSet(BaseModelFormSet):
    def __init__(self, fragment, section, is_coordinator, *args, **kwargs):
        super(BaseGradesFormSet, self).__init__(*args, **kwargs)
        self.fragment = fragment
        self.section = section
        self.is_coordinator = is_coordinator
        self.average = Decimal(000.0000)
        self.average_baseline = Decimal(000.0000)
        self.average_baseline_upper_boundary = Decimal(000.0000)
        self.average_baseline_lower_boundary = Decimal(000.0000)

    def clean(self):
        # don't validate for other boundary types or if the instructor is a coordinator
        if (self.fragment.boundary_type in [GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED,
                                            GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED_FIXED]
                and not self.is_coordinator):

            count = 0

            if self.fragment.entry_in_percentages:
                for form in self.forms:
                    # Don't include None values in averages
                    if form.cleaned_data['grade_percentage'] is not None:
                        self.average += form.cleaned_data['grade_percentage']
                        count += 1
            else:
                for form in self.forms:
                    # Don't include None values in averages
                    if form.cleaned_data['grade_quantity'] is not None:
                        self.average += form.cleaned_data['grade_quantity']
                        count += 1

            if count:
                self.average = self.average / count
                self.average = decimal(self.average)

            if self.fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED:
                self.average_baseline = StudentGrade.get_section_objective_average(self.section, self.fragment)

            elif self.fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED_FIXED:
                self.average_baseline = self.fragment.boundary_fixed_average or Decimal('0.0')

            self.average_baseline_upper_boundary = self.average_baseline + (self.fragment.boundary_range_upper or 0)
            self.average_baseline_lower_boundary = self.average_baseline - (self.fragment.boundary_range_lower or 0)

            if (self.average_baseline_upper_boundary < self.average
                    or self.average < self.average_baseline_lower_boundary):
                raise forms.ValidationError(
                    _('Section average {}% should be between {}% and {}%'.format(
                        self.average, self.average_baseline_lower_boundary, self.average_baseline_upper_boundary)))

        return super(BaseGradesFormSet, self).clean()


class GradeFragmentForm(forms.ModelForm):
    def __init__(self, semester, *args, **kwargs):
        super(GradeFragmentForm, self).__init__(*args, **kwargs)
        self.semester = semester
        unchanged_fields = ['weight', 'boundary_type', 'boundary_range_upper', 'boundary_range_lower',
                            'boundary_fixed_average']
        if not self.semester.can_create_grade_fragment():
            for field in self.fields:
                if field in unchanged_fields:
                    self.fields[field].disabled = True

    class Meta:
        model = GradeFragment
        fields = '__all__'
        exclude = ['updated_by', 'updated_on', 'course_offering', 'section']
        widgets = {
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'entry_start_date': forms.DateTimeInput(attrs={'class': 'form-control datetimepicker3'}),
            'entry_end_date': forms.DateTimeInput(attrs={'class': 'form-control datetimepicker3'}),
            'boundary_type': forms.Select(attrs={'class': 'form-control'}),
            'boundary_range_upper': forms.NumberInput(attrs={'class': 'form-control'}),
            'boundary_range_lower': forms.NumberInput(attrs={'class': 'form-control'}),
            'boundary_fixed_average': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        semester_start_date = self.semester.start_date
        semester_end_date = self.semester.end_date
        if not (semester_start_date <= self.cleaned_data['entry_start_date'].date() <=
                self.cleaned_data['entry_end_date'].date() <= semester_end_date):
            raise ValidationError([
                ValidationError(
                    _('entry dates should be between {} and {}'.format(semester_start_date, semester_end_date)))
            ])
        return self.cleaned_data


class BulkGradeFragmentForm(GradeFragmentForm):

    class Meta(GradeFragmentForm.Meta):
        exclude = GradeFragmentForm.Meta.exclude + ['boundary_type', 'category', 'description', 'weight', 'order']


class GradeFragmentsFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(GradeFragmentsFormSet, self).__init__(*args, **kwargs)
