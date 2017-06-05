from django import forms

from .models import StudentGrade, GradeFragment


class GradesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GradesForm, self).__init__(*args, **kwargs)
        max_value = GradeFragment.get_grade_fragment(self.initial['grade_fragment'])
        max_value = max_value.weight
        self.fields['grade_quantity'] = forms.DecimalField(
            max_value=max_value, min_value=0)

    class Meta:
        model = StudentGrade
        fields = ['enrollment', 'grade_fragment', 'grade_quantity', 'remarks']
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'thm-field'})
        }
