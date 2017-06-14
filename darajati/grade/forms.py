from django import forms
from django.forms import BaseModelFormSet
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import StudentGrade, GradeFragment

from enrollment.utils import today
from decimal import Decimal


class GradesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GradesForm, self).__init__(*args, **kwargs)
        self.fragment = GradeFragment.get_grade_fragment(self.initial['grade_fragment'])
        max_value = self.fragment.weight

        # IF entry in percent and there is grade value
        if self.fragment.entry_in_percentages and self.initial['grade_quantity']:
            self.fields['actual_grade'] = forms.DecimalField(
                decimal_places=settings.MAX_DECIMAL_POINT,
                max_digits=settings.MAX_DIGITS,
                required=False,
                widget=forms.NumberInput(attrs={'disabled': 'disabled', 'class': 'thm-field'}))

            self.fields['grade_quantity'] = forms.DecimalField(
                decimal_places=settings.MAX_DECIMAL_POINT,
                max_digits=settings.MAX_DIGITS,
                required=False,
                max_value=100, min_value=0,
                widget=forms.NumberInput(attrs={'class': 'thm-field'}))

            self.initial['actual_grade'] = self.initial['grade_quantity']

            # IF grade value was submitted once and it's not allowed to enter more then one time
            if self.initial['updated_on'] and not self.fragment.allow_change:
                self.fields['grade_quantity'] = forms.DecimalField(
                    decimal_places=settings.MAX_DECIMAL_POINT,
                    max_digits=settings.MAX_DIGITS,
                    required=False,
                    max_value=100, min_value=0,
                    widget=forms.NumberInput(attrs={'class': 'thm-field', 'readonly': 'True'}))
                self.fields['remarks'] = forms.CharField(widget=forms.TextInput(attrs={'class': 'thm-field',
                                                                                       'readonly': 'True'}))

            self.initial['grade_quantity'] = round((self.initial['grade_quantity'] * 100) / self.fragment.weight, 2)

        # IF entry not in percent and there is grade value
        elif not self.fragment.entry_in_percentages and self.initial['grade_quantity']:
            self.fields['grade_quantity'] = forms.DecimalField(
                max_value=max_value, min_value=0, required=False,
                widget=forms.NumberInput(attrs={'class': 'thm-field'}))

            # IF grade value was submitted once and it's not allowed to enter more then one time
            if self.initial['updated_on'] and not self.fragment.allow_change:
                self.fields['grade_quantity'] = forms.DecimalField(
                    max_value=max_value, min_value=0, required=False,
                    widget=forms.NumberInput(attrs={'class': 'thm-field', 'readonly': 'True'}))
                self.fields['remarks'] = forms.CharField(widget=forms.TextInput(attrs={'class': 'thm-field',
                                                                                       'readonly': 'True'}))
        else:
            self.fields['grade_quantity'] = forms.DecimalField(
                max_value=max_value, min_value=0, required=False,
                widget=forms.NumberInput(attrs={'class': 'thm-field'}))
            if self.fragment.entry_in_percentages:
                self.fields['grade_quantity'] = forms.DecimalField(
                    max_value=100, min_value=0, required=False,
                    widget=forms.NumberInput(attrs={'class': 'thm-field'}))

                self.fields['actual_grade'] = forms.DecimalField(
                    decimal_places=settings.MAX_DECIMAL_POINT,
                    max_digits=settings.MAX_DIGITS,
                    required=False,
                    widget=forms.NumberInput(attrs={'disabled': 'disabled', 'class': 'thm-field'}))

    def save(self, commit=True):
        self.instance.updated_by = self.user
        if ('grade_quantity' in self.changed_data or 'remarks' in self.changed_data) and \
                (self.cleaned_data['updated_on'] is None or self.fragment.allow_change):
            self.instance.updated_on = today()
            if self.fragment.entry_in_percentages and self.cleaned_data['grade_quantity']:
                self.instance.grade_quantity = (self.fragment.weight / 100) * self.cleaned_data['grade_quantity']
            return super(GradesForm, self).save()

    class Meta:
        model = StudentGrade
        fields = ['enrollment', 'grade_fragment', 'grade_quantity', 'remarks', 'updated_on']
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'thm-field'}),
            'enrollment': forms.HiddenInput(),
            'grade_fragment': forms.HiddenInput(),
            'updated_on': forms.HiddenInput(),
        }


class BaseGradesFormSet(BaseModelFormSet):
    def __init__(self, fragment, section, *args, **kwargs):
        super(BaseGradesFormSet, self).__init__(*args, **kwargs)
        self.fragment = fragment
        self.section = section
        self.average = Decimal(000.00)

    def clean(self):
        # if by somehow the grade was passed greater then what it should be it will accept it. Fix later
        for form in self.forms:
            if (not self.fragment.allow_change and form.cleaned_data['updated_on'] is not None) and \
                    ('grade_quantity' in form.changed_data or 'remarks' in form.changed_data):
                raise forms.ValidationError(_('You are not allowed to tamper with the grades'))

            self.average += form.cleaned_data['grade_quantity']

        if self.fragment.entry_in_percentages:

            self.average = round((self.fragment.weight / (100 * len(self.forms))) * self.average, 2)

        else:
            self.average = round(self.average / len(self.forms), 2)

        # This is for subjective bounded
        if self.fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED:
            objective_average = StudentGrade.get_section_objective_average(self.section)
            less_objective_average = objective_average - self.fragment.boundary_range
            more_objective_average = objective_average + self.fragment.boundary_range
            if self.fragment.boundary_range:
                if not less_objective_average <= self.average <= more_objective_average:
                    raise forms.ValidationError(
                        _('Section average {} should be between {} and {}'.format(
                            self.average, more_objective_average, less_objective_average)))
            else:
                raise forms.ValidationError(
                    _('Submitting Failed, Make sure the boundary range of this grade plan has a value'))

        # This is for subjective bounded fixed
        if self.fragment.boundary_type == GradeFragment.GradesBoundaries.SUBJECTIVE_BOUNDED_FIXED:
            pass
        return self.cleaned_data


class GradeFragmentForm(forms.ModelForm):
    class Meta:
        model = GradeFragment
        fields = '__all__'
        exclude = ['updated_by', 'updated_on', 'course_offering', 'section']
        widgets = {
            'category': forms.TextInput(attrs={'class': 'thm-field'}),
            'description': forms.TextInput(attrs={'class': 'thm-field'}),
            'weight': forms.NumberInput(attrs={'class': 'thm-field'}),
            'allow_entry': forms.CheckboxInput(attrs={'class': 'thm-field'}),
            'order': forms.NumberInput(attrs={'class': 'thm-field'}),
            'show_teacher_report': forms.CheckboxInput(attrs={'class': 'thm-field'}),
            'show_student_report': forms.CheckboxInput(attrs={'class': 'thm-field'}),
            'boundary_type': forms.Select(attrs={'class': 'thm-field'}),
            'boundary_range': forms.NumberInput(attrs={'class': 'thm-field'}),
            'boundary_fixed_average': forms.NumberInput(attrs={'class': 'thm-field'}),
            'allow_change': forms.CheckboxInput(attrs={'class': 'thm-field'}),
            'allow_subjective_marking': forms.CheckboxInput(attrs={'class': 'thm-field'}),
            'entry_in_percentages': forms.CheckboxInput(attrs={'class': 'thm-field'}),
        }
