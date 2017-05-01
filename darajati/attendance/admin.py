from django.contrib import admin
from .models import *

admin.site.register(ScheduledPeriod)
admin.site.register(AttendanceInstance)
admin.site.register(Attendance)
