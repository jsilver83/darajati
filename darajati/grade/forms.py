from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import StudentGrade, GradeFragment


class GradesForm(forms.ModelForm):
    # TODO: Fix the label name of grade quantity to make it dynamic
    def __init__(self, *args, **kwargs):
        super(GradesForm, self).__init__(*args, **kwargs)
        self.fragment = GradeFragment.get_grade_fragment(self.initial['grade_fragment'])
        max_value = self.fragment.weight

        if self.fragment.entry_in_percentages:
            # Set another field to show the actual grade
            self.fields['actual_grade'] = forms.DecimalField(
                required=False,
                widget=forms.NumberInput(attrs={'disable': 'disable', 'class': 'thm-field'}))
            self.initial['actual_grade'] = self.initial['grade_quantity']

            # Set some dynamic changes to the grade_quantity field
            self.fields['grade_quantity'].label = _('Student Grade in Percent')
            self.fields['grade_quantity'] = forms.DecimalField(
                max_value=100, min_value=0, widget=forms.NumberInput(attrs={'class': 'thm-field'}))
            self.initial['grade_quantity'] = (self.initial['grade_quantity'] * 100) / self.fragment.weight

        else:
            self.fields['grade_quantity'] = forms.DecimalField(
                max_value=max_value, min_value=0, widget=forms.NumberInput(attrs={'class': 'thm-field'}))

    class Meta:
        model = StudentGrade
        fields = ['enrollment', 'grade_fragment', 'grade_quantity', 'remarks']
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'thm-field'}),
            'enrollment': forms.Select(attrs={'class': 'thm-field'}),
            'grade_fragment': forms.Select(attrs={'class': 'thm-field'}),
        }

    def save(self, commit=True):
        self.instance.updated_by = self.user
        if self.fragment.entry_in_percentages:
            self.instance.grade_quantity = self.cleaned_data['grade_quantity'] * (
                self.fragment.weight / 100)
        return super(GradesForm, self).save()
