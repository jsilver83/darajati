from django.forms import ModelForm
from . models import *


class AttendanceForm(ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'
