from decimal import Decimal

from django import forms
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet
from django.utils.translation import ugettext_lazy as _

from darajati.utils import decimal
from .models import StudentGrade, GradeFragment, LetterGrade


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
            self.fields['grade_quantity'].widget = forms.HiddenInput()

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

        if self.instance.grade_quantity and not self.is_change_allowed:
            self.fields['grade_quantity'].widget.attrs.update({'readonly': 'True'})
            if self.instance.grade_fragment.entry_in_percentages:
                self.fields['grade_percentage'].widget.attrs.update({'readonly': 'True'})

    def clean(self):
        cleaned_data = super().clean()

        error_msg = _('You are not allowed to tamper with the grades')
        if (('grade_percentage' in self.changed_data or 'grade_quantity' in self.changed_data)
                and not self.is_change_allowed):
            if self.instance.grade_fragment.entry_in_percentages:
                initial_grade_quantity = self.instance.grade_quantity if self.instance.grade_quantity else decimal(0)
                initial_grade_percentage = decimal(initial_grade_quantity * 100 / self.instance.grade_fragment.weight)
                if (self.instance.grade_quantity and (initial_grade_percentage != cleaned_data.get('grade_percentage')
                        or self.instance.grade_quantity != cleaned_data.get('grade_quantity'))):
                    raise forms.ValidationError(error_msg)
            else:
                if self.instance.grade_quantity and self.instance.grade_quantity != cleaned_data.get('grade_quantity'):
                    raise forms.ValidationError(error_msg)

        return cleaned_data

    def save(self, commit=True):
        if ('grade_percentage' in self.changed_data or 'grade_quantity' in self.changed_data
                or 'remarks' in self.changed_data):
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
                self.average = decimal(self.average / count)

                if self.fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED:
                    self.average_baseline = StudentGrade.get_section_objective_average(self.section, self.fragment)

                elif self.fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED_FIXED:
                    self.average_baseline = self.fragment.boundary_fixed_average or Decimal('0.0')

                self.average_baseline_upper_boundary = self.average_baseline + (self.fragment.boundary_range_upper or 0)
                self.average_baseline_lower_boundary = self.average_baseline - (self.fragment.boundary_range_lower or 0)

                if (self.average_baseline_upper_boundary < self.average
                        or self.average < self.average_baseline_lower_boundary):
                    raise forms.ValidationError(
                        _('Section average {} should be between {} and {}'.format(
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
        exclude = GradeFragmentForm.Meta.exclude + ['boundary_type', 'category', 'description', 'weight', 'order',
                                                    'student_total_grading', 'entry_in_percentages']


class GradeFragmentsFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(GradeFragmentsFormSet, self).__init__(*args, **kwargs)


class LetterGradeForm(forms.ModelForm):
    def __init__(self, course_offering, upper_boundary, lower_boundary, user, *args, **kwargs):
        super(LetterGradeForm, self).__init__(*args, **kwargs)
        self.course_offering = course_offering
        self.user = user
        self.fields['cut_off_point'].validators.append(validators.MaxValueValidator(upper_boundary))
        self.fields['cut_off_point'].validators.append(validators.MinValueValidator(lower_boundary))

    class Meta:
        model = LetterGrade
        fields = '__all__'
        exclude = ['updated_by', 'updated_on', 'course_offering', 'section', ]
        widgets = {
            'course_offering': forms.HiddenInput(),
            'section': forms.HiddenInput(),
        }

    def save(self, commit=True):
        saved = super(LetterGradeForm, self).save(commit=False)
        saved.course_offering = self.course_offering
        saved.updated_by = self.user
        if commit:
            saved.save()
        return saved


class LetterGradesFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(LetterGradesFormSet, self).__init__(*args, **kwargs)


class GradeFragmentsExclusionForm(forms.Form):
    fragments_to_be_included = forms.MultipleChoiceField(
        label=_('Included Fragments'),
        help_text=_('Fragments to be included in the statistics')
    )

    def __init__(self, course_offering, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_offering = course_offering
        self.fields['fragments_to_be_included'].choices = [(fragment.pk, fragment.short_name)
                                                           for fragment in
                                                           GradeFragment.objects.filter(
                                                               course_offering=course_offering)]
