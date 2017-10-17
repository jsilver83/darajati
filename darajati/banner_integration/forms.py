from django import forms
from django.utils.translation import ugettext_lazy as _


class CourseOfferingForm(forms.Form):
    def __init__(self, choices, *args, **kwargs):
        super(CourseOfferingForm, self).__init__(*args, **kwargs)
        self.fields['course_offering'] = forms.ChoiceField(
            label=_('Course Offering'),
            choices=choices,
            required=True,
            widget=forms.Select(attrs={'class': 'thm-field'}))
        self.fields['commit_changes'] = forms.BooleanField(
            label=_('Commit changes'),
            required=False,
        )
        self.fields['detail_report'] = forms.BooleanField(
            label=_('Detail report'),
            required=False,
        )


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
