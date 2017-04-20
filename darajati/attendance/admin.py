from django.contrib import admin
from .models import *

admin.site.register(ScheduledPeriod)
admin.site.register(AttendanceInstant)
admin.site.register(Attendance)
