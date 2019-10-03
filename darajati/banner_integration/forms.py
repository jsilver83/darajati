from django import forms
from django.utils.translation import ugettext_lazy as _


class BannerSynchronizationForm(forms.Form):
    course_offering = forms.ChoiceField(
        label=_('Course Offering'),
        required=True,
        widget=forms.RadioSelect,
    )

    first_week_mode = forms.BooleanField(
        label=_('First Week Mode'),
        required=False,
        widget=forms.NullBooleanSelect(attrs={'class': 'form-control'}),
        help_text=_('You have to check this during the first two weeks of the semester only. Checking this after that '
                    'will make this process unnecessarily much slower')
    )

    update_students_data = forms.BooleanField(
        label=_('Update Students Data'),
        required=False,
        widget=forms.NullBooleanSelect(attrs={'class': 'form-control'}),
        help_text=_('You can check this if you wish to update student data (name, mobile, email) in this courses'
                    ' offering. You have to check this with the "First Week Mode"')
    )

    def __init__(self, choices, *args, **kwargs):
        super(BannerSynchronizationForm, self).__init__(*args, **kwargs)
        self.fields['course_offering'].choices = choices

    def clean(self):
        cleaned_data = super().clean()

        first_week_mode = cleaned_data.get('first_week_mode', False)
        update_students_data = cleaned_data.get('update_students_data', False)

        if update_students_data and not first_week_mode:
            raise forms.ValidationError(_('You have to check "Update Student Data" with "First Week Mode"'))

        return cleaned_data


class GradesImportForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(GradesImportForm, self).__init__(*args, **kwargs)
        self.fields['grade_fragment'] = forms.ChoiceField(
            label=_('Grade Fragment'),
            required=True,
            choices=choices,
            widget=forms.Select(attrs={'class': 'thm-field'})
        )
        self.fields['grade'] = forms.CharField(
            widget=forms.Textarea()
        )
        self.fields['commit'] = forms.BooleanField(
            label=_('Commit Changes'),
            required=False
        )
