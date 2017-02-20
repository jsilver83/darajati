from django.contrib import admin
from .models import *


admin.site.register(Student)
admin.site.register(Instructor)
admin.site.register(Semester)
admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Enrolment)
admin.site.register(ScheduledPeriod)
admin.site.register(AttendanceInstant)
admin.site.register(Attendance)
