# from django import forms
# from django.utils.translation import ugettext_lazy as _
#
#
# class GradesImportForm(forms.Form):
#     def __init__(self, *args, **kwargs):
#         super(GradesImportForm, self).__init__(*args, **kwargs)
#         self.fields['grade'] = forms.CharField(
#             widget=forms.Textarea(
#                 attrs={'placeholder': _(u'Please follow the format:\n\n'
#                                         u'student_id  mark  remark\n\n'
#                                         u'0000000000 9 -1 for not writing the name')})
#         )
#         self.fields['commit'] = forms.BooleanField(
#             label=_('Commit changes'),
#             required=False,
#             help_text=_('This checkbox is for you to save the changes you viewed in the report.')
#         )
