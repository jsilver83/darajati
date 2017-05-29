from django import forms

from .models import StudentGrade, GradeBreakDown


class GradesForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GradesForm, self).__init__(*args, **kwargs)
        max_value = GradeBreakDown.get_grade_break_down(self.initial['grade_break_down'])
        max_value = max_value.weight
        self.fields['grade_quantity'] = forms.DecimalField(
            max_value=max_value,
            min_value=0.0)

    class Meta:
        model = StudentGrade
        fields = ['enrollment', 'grade_break_down', 'grade_quantity', 'remarks']
