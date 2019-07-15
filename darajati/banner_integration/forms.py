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

    def __init__(self, choices, *args, **kwargs):
        super(BannerSynchronizationForm, self).__init__(*args, **kwargs)
        self.fields['course_offering'].choices = choices


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
