from django import forms
from django.utils.translation import ugettext_lazy as _


class CourseOfferingForm(forms.Form):
    def __init__(self, choices, *args, **kwargs):
        super(CourseOfferingForm, self).__init__(*args, **kwargs)
        self.fields['course_offering'] = forms.ChoiceField(label=_('Course Offering'),
                                                           choices=choices,
                                                           required=True,
                                                           widget=forms.Select(attrs={'class': 'thm-field'}))
